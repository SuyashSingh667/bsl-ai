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
import { synthesizeSpeech, Ticket } from '../services/api';
import { getApiBaseUrl } from '../services/config';
import { soundPlayer } from '../services/soundPlayer';

interface PrecautionaryMeasuresScreenProps {
  ticket: Ticket;
  onProceedToResult: () => void;
}

const DEFAULT_HINDI_MEASURES = [
  {
    id: 'evacuate',
    icon: '🏃',
    title: 'Immediate Evacuation & Cordon',
    title_native: 'तत्काल निकासी एवं सुरक्षा घेरा',
    text_native: 'खतरे के प्रभाव क्षेत्र से तुरंत सुरक्षित दूरी (कम से कम 100 मीटर) पर जाएं और हवा की विपरीत दिशा में रहें।',
    checklist_label_native: 'सुरक्षा घेरा तुरंत स्थापित किया',
  },
  {
    id: 'life_safety_ppe',
    icon: '🛡️',
    title: 'Mandatory PPE Compliance',
    title_native: 'अनिवार्य सुरक्षा उपकरण (PPE)',
    text_native: 'उचित सुरक्षा उपकरण (SCBA / रासायनिक चश्मा / सेफ्टी सूट) पहने बिना प्रभावित उपकरण के समीप न जाएं।',
    checklist_label_native: 'सुरक्षा गियर की पुष्टि की गई',
  },
  {
    id: 'donts',
    icon: '⛔',
    title: 'Prohibited Immediate Actions',
    title_native: 'प्रतिबंधित गतिविधियां',
    text_native: 'बिजली या तेल की आग पर पानी न डालें; बिना लिखित अनुमति मशीन को दोबारा चालू करने का प्रयास न करें।',
    checklist_label_native: 'गलत कदम उठाने से परहेज किया',
  },
  {
    id: 'emergency_contacts',
    icon: '📞',
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
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isPlayingFullAudio, setIsPlayingFullAudio] = useState<boolean>(false);
  const [playingMeasureKey, setPlayingMeasureKey] = useState<string | number | null>(null);
  const [loadingMeasureKey, setLoadingMeasureKey] = useState<string | number | null>(null);

  const isHindi = !ticket.language || ticket.language === 'hi';
  const precautions = ticket.precautionary_measures;
  const measuresList: any[] =
    precautions?.measures ||
    precautions?.measures_localized ||
    DEFAULT_HINDI_MEASURES;

  // Play full spoken summary audio briefing
  const playFullGuidanceAudio = async (targetUri?: string) => {
    const uriToPlay = targetUri || audioUrl;
    if (!uriToPlay) return;
    setPlayingMeasureKey(null);
    await soundPlayer.playUrl(uriToPlay, (playing) => {
      setIsPlayingFullAudio(playing);
    });
  };

  // Play specific individual measure card aloud in native language
  const playIndividualMeasureAudio = async (m: any, key: string | number) => {
    try {
      // If already playing this item, stop it
      if (playingMeasureKey === key) {
        await soundPlayer.stop();
        setPlayingMeasureKey(null);
        return;
      }

      await soundPlayer.stop();
      setIsPlayingFullAudio(false);
      setLoadingMeasureKey(key);

      // Determine the exact speech text
      const titleText = typeof m === 'object' ? (m.title_native || m.title || '') : '';
      const bodyText = typeof m === 'object' ? (m.text_native || m.text || m.checklist_label_native || '') : String(m);
      const textToSpeak = titleText ? `${titleText}। ${bodyText}` : bodyText;

      const lang = ticket.language || 'hi';
      const synthesizedUrl = await synthesizeSpeech(textToSpeak, lang);

      setLoadingMeasureKey(null);
      setPlayingMeasureKey(key);

      await soundPlayer.playUrl(synthesizedUrl, (playing) => {
        if (!playing) {
          setPlayingMeasureKey(null);
        }
      });
    } catch (err: any) {
      setLoadingMeasureKey(null);
      setPlayingMeasureKey(null);
      console.warn('Could not read measure aloud:', err);
    }
  };

  useEffect(() => {
    const resolveAudio = async () => {
      const path = precautions?.audio_path || ticket.guidance_audio_path;
      if (path) {
        const base = await getApiBaseUrl();
        const fullUrl = path.startsWith('http') ? path : `${base}${path}`;
        setAudioUrl(fullUrl);
        // Auto-play spoken guidance summary
        playFullGuidanceAudio(fullUrl);
      }
    };
    resolveAudio();
    return () => {
      soundPlayer.stop();
    };
  }, [ticket]);

  const handleProceed = async () => {
    await soundPlayer.stop();
    setIsPlayingFullAudio(false);
    setPlayingMeasureKey(null);
    onProceedToResult();
  };

  return (
    <View style={styles.container}>
      <StepIndicator currentStep={4} />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Header with Bilingual Title */}
        <View style={styles.alertHeader}>
          <View style={styles.iconCircle}>
            <Text style={styles.iconText}>🛡️</Text>
          </View>
          <View style={styles.headerTitles}>
            <Text style={styles.title}>
              {isHindi ? 'व्यक्तिगत सुरक्षा सावधानियां' : 'Personal Safety Precautions'}
            </Text>
            <Text style={styles.subtitle}>
              {isHindi
                ? 'बोकारो स्टील प्लांट मानक संचालन प्रक्रिया (BSL SOP)'
                : 'Grounded in BSL Safety Operating Standard SOP'}
            </Text>
          </View>
        </View>

        {/* Master Audio Briefing Button */}
        {audioUrl && (
          <TouchableOpacity
            style={[styles.audioBriefingButton, isPlayingFullAudio && styles.audioBriefingButtonPlaying]}
            onPress={() => playFullGuidanceAudio(audioUrl)}
          >
            <Text style={styles.audioIcon}>{isPlayingFullAudio ? '🔊' : '🔈'}</Text>
            <View style={styles.audioTextWrapper}>
              <Text style={styles.audioButtonTitle}>
                {isPlayingFullAudio
                  ? 'संपूर्ण सुरक्षा निर्देश सुना जा रहा है...'
                  : 'संपूर्ण सुरक्षा निर्देश सुनें (Listen to All)'}
              </Text>
              <Text style={styles.audioButtonSub}>
                {isPlayingFullAudio
                  ? 'रोकने या दोबारा सुनने के लिए टैप करें'
                  : 'फ़ोन स्पीकर से सभी सुरक्षा उपायों का संक्षिप्त विवरण सुनें'}
              </Text>
            </View>
          </TouchableOpacity>
        )}

        {/* Action Directives Section Header */}
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionHeader}>
            {isHindi ? 'अनिवार्य तत्काल कार्रवाई' : 'Mandatory Immediate Actions'}:
          </Text>
          <Text style={styles.sectionSubHeader}>
            {isHindi ? 'प्रत्येक कार्ड को अलग से सुन सकते हैं' : 'Tap 🔊 to read each action aloud'}
          </Text>
        </View>

        {/* Action Directives Cards */}
        {measuresList.map((m: any, idx: number) => {
          const key = m.id || idx;
          const isItemPlaying = playingMeasureKey === key;
          const isItemLoading = loadingMeasureKey === key;

          // Extract native first, fallback to standard
          const titleNative = typeof m === 'object' ? (m.title_native || m.title || '') : '';
          const titleEn = typeof m === 'object' && m.title_native && m.title && m.title !== m.title_native ? m.title : '';
          const textNative = typeof m === 'object' ? (m.text_native || m.text || m.checklist_label_native || JSON.stringify(m)) : String(m);
          const checklistLabel = typeof m === 'object' ? (m.checklist_label_native || m.checklist_label || '') : '';
          const icon = typeof m === 'object' && m.icon ? m.icon : '⚠️';

          return (
            <View
              key={idx}
              style={[styles.measureItem, isItemPlaying && styles.measureItemPlaying]}
            >
              <View style={styles.bulletNumber}>
                <Text style={styles.bulletText}>{icon}</Text>
              </View>

              <View style={styles.measureContent}>
                {/* Titles */}
                <View style={styles.titleRow}>
                  <Text style={styles.measureTitle}>{titleNative || `कार्रवाई ${idx + 1}`}</Text>
                  {titleEn ? <Text style={styles.measureTitleSub}>({titleEn})</Text> : null}
                </View>

                {/* Body Text in Native Language */}
                <Text style={styles.measureText}>{textNative}</Text>

                {/* Action Checklist Tag if available */}
                {checklistLabel ? (
                  <View style={styles.checklistBadge}>
                    <Text style={styles.checklistBadgeText}>✓ {checklistLabel}</Text>
                  </View>
                ) : null}

                {/* Dedicated Read Aloud Button for this Action */}
                <TouchableOpacity
                  style={[
                    styles.readAloudButton,
                    isItemPlaying && styles.readAloudButtonPlaying,
                  ]}
                  onPress={() => playIndividualMeasureAudio(m, key)}
                  disabled={isItemLoading}
                  activeOpacity={0.8}
                >
                  {isItemLoading ? (
                    <ActivityIndicator size="small" color="#38bdf8" />
                  ) : (
                    <Text style={styles.readAloudIcon}>{isItemPlaying ? '⏹️' : '🔊'}</Text>
                  )}
                  <Text style={styles.readAloudText}>
                    {isItemLoading
                      ? 'आवाज़ तैयार हो रही है...'
                      : isItemPlaying
                      ? 'रोकें (Stop Reading)'
                      : 'इसे बोलकर सुनें (Read Aloud)'}
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          );
        })}

        {/* Completion Proceed Button */}
        <TouchableOpacity style={styles.proceedButton} onPress={handleProceed}>
          <Text style={styles.proceedButtonText}>
            {isHindi ? 'अंतिम सुरक्षा टिकट एवं डॉसियर देखें ➔' : 'View Final Safety Ticket & Dossier ➔'}
          </Text>
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#070d18',
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 40,
  },
  alertHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 18,
  },
  iconCircle: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(56, 189, 248, 0.15)',
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
    fontSize: 19,
    fontWeight: '800',
    marginBottom: 3,
  },
  subtitle: {
    color: '#38bdf8',
    fontSize: 12,
    fontWeight: '600',
  },
  audioBriefingButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0f172a',
    borderRadius: 14,
    padding: 16,
    borderWidth: 1.5,
    borderColor: '#38bdf8',
    marginBottom: 20,
  },
  audioBriefingButtonPlaying: {
    backgroundColor: 'rgba(56, 189, 248, 0.15)',
    borderColor: '#0284c7',
  },
  audioIcon: {
    fontSize: 28,
    marginRight: 14,
  },
  audioTextWrapper: {
    flex: 1,
  },
  audioButtonTitle: {
    color: '#38bdf8',
    fontSize: 14,
    fontWeight: '700',
    marginBottom: 2,
  },
  audioButtonSub: {
    color: '#94a3b8',
    fontSize: 11,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  sectionHeader: {
    color: '#cbd5e1',
    fontSize: 13,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  sectionSubHeader: {
    color: '#38bdf8',
    fontSize: 11,
    fontWeight: '600',
  },
  measureItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#0c1626',
    borderRadius: 14,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1.5,
    borderColor: '#1e293b',
  },
  measureItemPlaying: {
    borderColor: '#38bdf8',
    backgroundColor: 'rgba(56, 189, 248, 0.08)',
  },
  bulletNumber: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(56, 189, 248, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
    marginTop: 2,
  },
  bulletText: {
    fontSize: 16,
  },
  measureContent: {
    flex: 1,
  },
  titleRow: {
    marginBottom: 6,
  },
  measureTitle: {
    color: '#38bdf8',
    fontSize: 15,
    fontWeight: '700',
    lineHeight: 20,
  },
  measureTitleSub: {
    color: '#64748b',
    fontSize: 11,
    fontWeight: '600',
    marginTop: 1,
  },
  measureText: {
    color: '#f1f5f9',
    fontSize: 13,
    lineHeight: 20,
    fontWeight: '500',
    marginBottom: 8,
  },
  checklistBadge: {
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: 'rgba(16, 185, 129, 0.3)',
    marginBottom: 10,
  },
  checklistBadgeText: {
    color: '#34d399',
    fontSize: 11,
    fontWeight: '600',
  },
  readAloudButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1e293b',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 8,
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderColor: '#334155',
  },
  readAloudButtonPlaying: {
    backgroundColor: 'rgba(56, 189, 248, 0.2)',
    borderColor: '#38bdf8',
  },
  readAloudIcon: {
    fontSize: 14,
    marginRight: 6,
  },
  readAloudText: {
    color: '#38bdf8',
    fontSize: 12,
    fontWeight: '700',
  },
  proceedButton: {
    backgroundColor: '#059669',
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 20,
  },
  proceedButtonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '700',
  },
});
