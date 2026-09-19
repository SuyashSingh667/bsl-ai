import React, { useState, useEffect } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { StepIndicator } from '../components/StepIndicator';
import { getPrecautionaryMeasures, Ticket } from '../services/api';
import { getApiBaseUrl } from '../services/config';
import { soundPlayer } from '../services/soundPlayer';

interface PrecautionaryMeasuresScreenProps {
  ticket: Ticket;
  onProceedToResult: () => void;
}

const DEFAULT_HINDI_MEASURES = [
  {
    id: 'evacuate',
    icon: '',
    title: 'Immediate Evacuation & Cordon',
    title_native: 'तत्काल निकासी एवं सुरक्षा घेरा',
    text_native: 'खतरे के प्रभाव क्षेत्र से तुरंत सुरक्षित दूरी (कम से कम 100 मीटर) पर जाएं और हवा की विपरीत दिशा में रहें।',
    checklist_label_native: 'सुरक्षा घेरा तुरंत स्थापित किया',
  },
  {
    id: 'life_safety_ppe',
    icon: '',
    title: 'Mandatory PPE Compliance',
    title_native: 'अनिवार्य सुरक्षा उपकरण (PPE)',
    text_native: 'उचित सुरक्षा उपकरण (SCBA / रासायनिक चश्मा / सेफ्टी सूट) पहने बिना प्रभावित उपकरण के समीप न जाएं।',
    checklist_label_native: 'सुरक्षा गियर की पुष्टि की गई',
  },
  {
    id: 'donts',
    icon: '',
    title: 'Prohibited Immediate Actions',
    title_native: 'प्रतिबंधित गतिविधियां',
    text_native: 'बिजली या तेल की आग पर पानी न डालें; बिना लिखित अनुमति मशीन को दोबारा चालू करने का प्रयास न करें।',
    checklist_label_native: 'गलत कदम उठाने से परहेज किया',
  },
  {
    id: 'emergency_contacts',
    icon: '',
    title: 'Incident Command Notification',
    title_native: 'इमरजेंसी कंट्रोल एवं एम्बुलेंस',
    text_native: 'प्लांट फायर स्टेशन (101) एवं मेडिकल ट्रॉमा एम्बुलेंस (102) को सूचित करें और प्रभावित कर्मियों की हाजिरी लें।',
    checklist_label_native: 'कंट्रोल रूम 101/102 को सूचित किया',
  },
];

export const PrecautionaryMeasuresScreen: React.FC<PrecautionaryMeasuresScreenProps> = ({
  ticket,
  onProceedToResult,
}) => {
  const [precautionsData, setPrecautionsData] = useState<any>(ticket.precautionary_measures);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isPlayingFullAudio, setIsPlayingFullAudio] = useState<boolean>(false);
  const [isLoadingPrecautions, setIsLoadingPrecautions] = useState<boolean>(false);

  // Interactive Checklist State: map measure ID or index to boolean checked state
  const [checkedItems, setCheckedItems] = useState<Record<string, boolean>>({});

  const isHindi = !ticket.language || ticket.language === 'hi';

  const measuresList: any[] =
    precautionsData?.measures ||
    precautionsData?.measures_localized ||
    ticket.precautionary_measures?.measures ||
    DEFAULT_HINDI_MEASURES;

  // Toggle checklist checkbox state
  const toggleCheckItem = (id: string) => {
    setCheckedItems((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  // Play or stop the master spoken guidance briefing audio
  const toggleFullGuidanceAudio = async () => {
    if (isPlayingFullAudio) {
      await soundPlayer.stop();
      setIsPlayingFullAudio(false);
      return;
    }

    // Build spoken text for offline fallback
    const spokenText =
      (isHindi
        ? precautionsData?.spoken_summary_hi || ticket.guidance_text_native
        : precautionsData?.spoken_summary_en || ticket.guidance_text) ||
      measuresList.map((m: any) => m.instruction || m.title).join('. ');

    const lang = ticket.language || (isHindi ? 'hi' : 'en');

    await soundPlayer.playUrlOrSpeak(audioUrl, spokenText, lang, (playing) => {
      setIsPlayingFullAudio(playing);
    });
  };

  // On mount: Fetch dynamic personalized measures if ticket ID is available
  useEffect(() => {
    let isMounted = true;

    const loadPrecautions = async () => {
      try {
        if (ticket.id) {
          setIsLoadingPrecautions(true);
          const freshPrecautions = await getPrecautionaryMeasures(ticket.id);
          if (isMounted && freshPrecautions) {
            setPrecautionsData(freshPrecautions);
            const path = freshPrecautions.audio_path || freshPrecautions.spoken_audio_path;
            if (path) {
              const base = await getApiBaseUrl();
              const fullUrl = path.startsWith('http') ? path : `${base}${path}`;
              setAudioUrl(fullUrl);
            }
          }
        }
      } catch (err) {
        console.warn('Could not refresh dynamic precautions:', err);
      } finally {
        if (isMounted) setIsLoadingPrecautions(false);
      }
    };

    // If we already have audio_path in initial ticket
    const initialAudioPath =
      ticket.precautionary_measures?.audio_path ||
      ticket.precautionary_measures?.spoken_audio_path ||
      ticket.guidance_audio_path;

    if (initialAudioPath) {
      getApiBaseUrl().then((base) => {
        if (isMounted) {
          const fullUrl = initialAudioPath.startsWith('http') ? initialAudioPath : `${base}${initialAudioPath}`;
          setAudioUrl(fullUrl);
        }
      });
    }

    loadPrecautions();

    return () => {
      isMounted = false;
      soundPlayer.stop();
    };
  }, [ticket.id]);

  const handleProceed = async () => {
    await soundPlayer.stop();
    setIsPlayingFullAudio(false);
    onProceedToResult();
  };

  const totalCount = measuresList.length;
  const checkedCount = measuresList.filter((m, idx) => checkedItems[m.id || String(idx)]).length;
  const progressPercent = totalCount > 0 ? Math.round((checkedCount / totalCount) * 100) : 0;
  const allChecked = totalCount > 0 && checkedCount === totalCount;

  return (
    <View style={styles.container}>
      <StepIndicator currentStep={4} />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Safety-Critical AI Disclaimer Banner */}
        <View style={styles.aiDisclaimerBanner}>
          <View style={styles.aiDisclaimerTextWrap}>
            <Text style={styles.aiDisclaimerTitle}>
              {isHindi
                ? 'एआई-जनित सुरक्षा सलाह — सुपरवाइजर से पुष्टि करें'
                : 'AI-Generated Guidance — Verify with Supervisor'}
            </Text>
            <Text style={styles.aiDisclaimerSub}>
              {isHindi
                ? 'सभी उपाय बोकारो स्टील प्लांट अनुमोदित एसओपी (SOP) से लिए गए हैं। आपात स्थिति में सुपरवाइजर के आदेश का पालन करें।'
                : 'Retrieve-and-quote citations from approved BSL SOPs. In an emergency, obey shift in-charge orders.'}
            </Text>
          </View>
        </View>

        {precautionsData?.sop_gap_detected ? (
          <View style={styles.sopGapBanner}>
            <View style={styles.sopGapTextWrap}>
              <Text style={styles.sopGapTitle}>
                {isHindi ? 'एसओपी अंतर पाया गया (SOP Gap Detected)' : 'SOP Gap Detected'}
              </Text>
              <Text style={styles.sopGapSub}>
                {isHindi
                  ? 'इस घटना के लिए कोई अनुमोदित एसओपी उपलब्ध नहीं है। सार्वभौमिक सुरक्षित प्रोटोकॉल सक्रिय है।'
                  : 'No approved SOP exists for this exact condition. Universal safe evacuation protocol is active.'}
              </Text>
            </View>
          </View>
        ) : null}

        {/* Header with Bilingual Title */}
        <View style={styles.alertHeader}>
          <View style={styles.headerTitles}>
            <Text style={styles.title}>
              {isHindi ? 'व्यक्तिगत सुरक्षा सावधानियां' : 'Personal Safety Precautions'}
            </Text>
            <Text style={styles.subtitle}>
              {precautionsData?.sop_source || (isHindi ? 'बोकारो स्टील प्लांट मानक संचालन प्रक्रिया (BSL SOP)' : 'BSL Safety SOP Standard')}
            </Text>
          </View>
        </View>

        {/* Personalized Context Badge */}
        <View style={styles.personalizedBanner}>
          <View style={styles.personalizedBadge}>
            <Text style={styles.personalizedBadgeText}>
              {isHindi
                ? 'आपके साक्षात्कार व सत्यापन उत्तरों के आधार पर तैयार व्यक्तिगत निर्देश'
                : 'Conditioned on your interview answers & verified on-site findings'}
            </Text>
          </View>
        </View>

        {/* Master Audio Briefing Player (Single Unified Briefing) */}
        {audioUrl ? (
          <TouchableOpacity
            style={[styles.audioBriefingButton, isPlayingFullAudio && styles.audioBriefingButtonPlaying]}
            onPress={toggleFullGuidanceAudio}
            activeOpacity={0.85}
          >
            <View style={styles.audioIconBox}>
              <Text style={styles.audioIcon}>{isPlayingFullAudio ? '■' : '▶'}</Text>
            </View>
            <View style={styles.audioTextWrapper}>
              <View style={styles.audioTitleRow}>
                <Text style={styles.audioButtonTitle}>
                  {isPlayingFullAudio
                    ? (isHindi ? 'ऑडियो बंद करें (Stop Audio)' : 'Stop Audio Briefing')
                    : (isHindi ? 'संपूर्ण सुरक्षा निर्देश सुनें (Listen to Full Briefing)' : 'Listen to Full Safety Briefing')}
                </Text>
                {isPlayingFullAudio && (
                  <View style={styles.liveAudioBadge}>
                    <Text style={styles.liveAudioBadgeText}>PLAYING</Text>
                  </View>
                )}
              </View>
              <Text style={styles.audioButtonSub}>
                {isPlayingFullAudio
                  ? (isHindi ? 'सभी सावधानियों का ऑडियो विवरण चल रहा है...' : 'Audio briefing is playing...')
                  : (isHindi ? 'फ़ोन स्पीकर से सभी सुरक्षा उपायों का संक्षिप्त विवरण एक साथ सुनें' : 'Listen to all safety measures sequentially aloud')}
              </Text>
            </View>
          </TouchableOpacity>
        ) : null}

        {/* Interactive Checklist Progress Card */}
        <View style={styles.complianceCard}>
          <View style={styles.complianceHeaderRow}>
            <View style={styles.complianceTitleGroup}>
              <Text style={styles.complianceTitle}>
                {isHindi ? 'सुरक्षा अनुपालन चेकलिस्ट' : 'Safety Compliance Checklist'}
              </Text>
              <Text style={styles.complianceSub}>
                {isHindi
                  ? 'कार्रवाई पूरी होने पर प्रत्येक बॉक्स पर टैप कर टिक करें'
                  : 'Tap each item to verify completion on-site'}
              </Text>
            </View>
            <View style={[styles.complianceCountPill, allChecked && styles.complianceCountPillDone]}>
              <Text style={styles.complianceCountText}>
                {checkedCount} / {totalCount} {isHindi ? 'पूर्ण' : 'Done'}
              </Text>
            </View>
          </View>

          {/* Progress Bar */}
          <View style={styles.progressBarTrack}>
            <View
              style={[
                styles.progressBarFill,
                { width: `${progressPercent}%` },
                allChecked && styles.progressBarFillDone,
              ]}
            />
          </View>
        </View>

        {/* Section Header */}
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionHeader}>
            {isHindi ? 'अनिवार्य सुरक्षा कदम (चेकलिस्ट)' : 'Mandatory Safety Action Checklist'}:
          </Text>
          {isLoadingPrecautions && (
            <ActivityIndicator size="small" color="#ffffff" style={{ marginLeft: 8 }} />
          )}
        </View>

        {/* Interactive Checklist Cards */}
        {measuresList.map((m: any, idx: number) => {
          const key = m.id || String(idx);
          const isChecked = !!checkedItems[key];

          const titleNative = typeof m === 'object' ? (m.title_native || m.title || '') : '';
          const titleEn = typeof m === 'object' && m.title_native && m.title && m.title !== m.title_native ? m.title : '';
          const textNative = typeof m === 'object' ? (m.text_native || m.text || m.checklist_label_native || JSON.stringify(m)) : String(m);
          const checklistLabel = typeof m === 'object' ? (m.checklist_label_native || m.checklist_label || '') : '';

          return (
            <TouchableOpacity
              key={key}
              style={[
                styles.checklistItemCard,
                isChecked && styles.checklistItemCardChecked,
              ]}
              onPress={() => toggleCheckItem(key)}
              activeOpacity={0.8}
            >
              {/* Left Column: Interactive Checkbox Square */}
              <View style={styles.checkboxContainer}>
                <View
                  style={[
                    styles.checkboxBox,
                    isChecked && styles.checkboxBoxChecked,
                  ]}
                >
                  <Text style={[styles.checkboxCheckmark, isChecked && styles.checkboxCheckmarkChecked]}>
                    {isChecked ? '✓' : ''}
                  </Text>
                </View>
              </View>

              {/* Right Column: Measure Content */}
              <View style={styles.cardContent}>
                {/* Title Row */}
                <View style={styles.titleRow}>
                  <Text style={[styles.measureTitle, isChecked && styles.measureTitleChecked]}>
                    {titleNative || `सुरक्षा उपाय ${idx + 1}`}
                  </Text>
                  {titleEn ? <Text style={styles.measureTitleSub}>({titleEn})</Text> : null}
                </View>

                {/* Body Text in Native Language */}
                <Text style={[styles.measureText, isChecked && styles.measureTextChecked]}>
                  {textNative}
                </Text>

                {/* SOP Citation Tag */}
                {m.citation ? (
                  <View style={styles.sopCitationBadge}>
                    <Text style={styles.sopCitationBadgeText}>SOP: {m.citation}</Text>
                  </View>
                ) : null}

                {/* Concrete Field Verification Action Tag */}
                {checklistLabel ? (
                  <View style={[styles.checklistBadge, isChecked && styles.checklistBadgeChecked]}>
                    <Text style={[styles.checklistBadgeText, isChecked && styles.checklistBadgeTextChecked]}>
                      {isChecked ? '✓ सत्यापित (Verified): ' : '☐ '}
                      {checklistLabel}
                    </Text>
                  </View>
                ) : null}
              </View>
            </TouchableOpacity>
          );
        })}

        {/* Completion Proceed Button */}
        <TouchableOpacity
          style={[styles.proceedButton, allChecked && styles.proceedButtonDone]}
          onPress={handleProceed}
          activeOpacity={0.85}
        >
          <Text style={styles.proceedButtonText}>
            {allChecked
              ? (isHindi ? '✓ सभी सुरक्षा उपायों की पुष्टि हुई — डॉसियर देखें ➔' : '✓ All Safety Measures Verified — View Dossier ➔')
              : (isHindi ? `सुरक्षा टिकट एवं डॉसियर देखें (${checkedCount}/${totalCount} पूर्ण) ➔` : `View Final Safety Ticket (${checkedCount}/${totalCount} verified) ➔`)}
          </Text>
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 50,
  },
  alertHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  iconCircle: {
    width: 48,
    height: 48,
    borderRadius: 16,
    backgroundColor: '#2c2c2e',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  iconText: {
    fontSize: 24,
  },
  headerTitles: {
    flex: 1,
  },
  title: {
    color: '#ffffff',
    fontSize: 20,
    fontWeight: '700',
    letterSpacing: -0.3,
  },
  subtitle: {
    color: 'rgba(235, 235, 245, 0.65)',
    fontSize: 13,
    marginTop: 2,
    letterSpacing: -0.1,
  },
  personalizedBanner: {
    marginBottom: 14,
  },
  personalizedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1c1c1e',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.15)',
    borderRadius: 16,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  personalizedBadgeIcon: {
    fontSize: 16,
    marginRight: 8,
  },
  personalizedBadgeText: {
    color: 'rgba(235, 235, 245, 0.85)',
    fontSize: 13,
    fontWeight: '500',
    flex: 1,
    lineHeight: 18,
  },
  audioBriefingButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1c1c1e',
    borderRadius: 20,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
  },
  audioBriefingButtonPlaying: {
    backgroundColor: '#2c2c2e',
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  audioIconBox: {
    width: 44,
    height: 44,
    borderRadius: 14,
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  audioIcon: {
    fontSize: 20,
  },
  audioTextWrapper: {
    flex: 1,
  },
  audioTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  audioButtonTitle: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '600',
    flex: 1,
    letterSpacing: -0.2,
  },
  liveAudioBadge: {
    backgroundColor: '#3a3a3c',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 9999,
    marginLeft: 6,
  },
  liveAudioBadgeText: {
    color: '#ffffff',
    fontSize: 10,
    fontWeight: '700',
  },
  audioButtonSub: {
    color: 'rgba(235, 235, 245, 0.65)',
    fontSize: 12,
    marginTop: 3,
    lineHeight: 16,
  },
  complianceCard: {
    backgroundColor: '#1c1c1e',
    borderRadius: 20,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
  },
  complianceHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  complianceTitleGroup: {
    flex: 1,
  },
  complianceTitle: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '600',
    letterSpacing: -0.2,
  },
  complianceSub: {
    color: 'rgba(235, 235, 245, 0.45)',
    fontSize: 12,
    marginTop: 2,
  },
  complianceCountPill: {
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 9999,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
  },
  complianceCountPillDone: {
    backgroundColor: '#2c2c2e',
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  complianceCountText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '600',
  },
  progressBarTrack: {
    height: 6,
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: '#ffffff',
    borderRadius: 3,
  },
  progressBarFillDone: {
    backgroundColor: '#ffffff',
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionHeader: {
    color: 'rgba(235, 235, 245, 0.45)',
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 0.2,
    textTransform: 'uppercase',
  },
  checklistItemCard: {
    flexDirection: 'row',
    backgroundColor: '#1c1c1e',
    borderRadius: 20,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
  },
  checklistItemCardChecked: {
    borderColor: 'rgba(255, 255, 255, 0.3)',
    backgroundColor: '#242426',
  },
  checkboxContainer: {
    alignItems: 'center',
    marginRight: 14,
    paddingTop: 2,
  },
  checkboxBox: {
    width: 26,
    height: 26,
    borderRadius: 8,
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.3)',
    backgroundColor: 'transparent',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  checkboxBoxChecked: {
    borderColor: '#ffffff',
    backgroundColor: '#ffffff',
  },
  checkboxCheckmark: {
    color: 'transparent',
    fontSize: 16,
    fontWeight: '900',
  },
  checkboxCheckmarkChecked: {
    color: '#000000',
  },
  cardCategoryIcon: {
    fontSize: 20,
  },
  cardContent: {
    flex: 1,
  },
  titleRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
    marginBottom: 6,
  },
  measureTitle: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '600',
    marginRight: 6,
    letterSpacing: -0.2,
  },
  measureTitleChecked: {
    color: '#ffffff',
  },
  measureTitleSub: {
    color: 'rgba(235, 235, 245, 0.45)',
    fontSize: 12,
  },
  measureText: {
    color: 'rgba(235, 235, 245, 0.7)',
    fontSize: 13,
    lineHeight: 19,
    marginBottom: 8,
  },
  measureTextChecked: {
    color: 'rgba(235, 235, 245, 0.5)',
  },
  checklistBadge: {
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 9999,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
  },
  checklistBadgeChecked: {
    backgroundColor: 'rgba(255, 255, 255, 0.12)',
    borderColor: 'rgba(255, 255, 255, 0.25)',
  },
  checklistBadgeText: {
    color: 'rgba(235, 235, 245, 0.7)',
    fontSize: 12,
    fontWeight: '600',
  },
  checklistBadgeTextChecked: {
    color: '#ffffff',
  },
  proceedButton: {
    backgroundColor: '#ffffff',
    minHeight: 52,
    borderRadius: 9999,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 12,
  },
  proceedButtonDone: {
    backgroundColor: '#ffffff',
  },
  proceedButtonText: {
    color: '#000000',
    fontSize: 15,
    fontWeight: '600',
    letterSpacing: -0.2,
  },
  aiDisclaimerBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1c1c1e',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.15)',
    borderRadius: 18,
    padding: 14,
    marginBottom: 14,
  },
  aiDisclaimerIcon: {
    fontSize: 24,
    marginRight: 10,
  },
  aiDisclaimerTextWrap: {
    flex: 1,
  },
  aiDisclaimerTitle: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '700',
    marginBottom: 2,
  },
  aiDisclaimerSub: {
    color: 'rgba(235, 235, 245, 0.7)',
    fontSize: 12,
    lineHeight: 16,
  },
  sopGapBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1c1c1e',
    borderWidth: 1,
    borderColor: 'rgba(255, 69, 58, 0.35)',
    borderRadius: 18,
    padding: 14,
    marginBottom: 14,
  },
  sopGapIcon: {
    fontSize: 24,
    marginRight: 10,
  },
  sopGapTextWrap: {
    flex: 1,
  },
  sopGapTitle: {
    color: '#FF453A',
    fontSize: 13,
    fontWeight: '700',
    marginBottom: 2,
  },
  sopGapSub: {
    color: 'rgba(235, 235, 245, 0.7)',
    fontSize: 12,
    lineHeight: 16,
  },
  sopCitationBadge: {
    alignSelf: 'flex-start',
    backgroundColor: '#1c1c1e',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.15)',
    borderRadius: 9999,
    paddingHorizontal: 10,
    paddingVertical: 4,
    marginBottom: 8,
  },
  sopCitationBadgeText: {
    color: 'rgba(235, 235, 245, 0.75)',
    fontSize: 11,
    fontWeight: '600',
  },
});
