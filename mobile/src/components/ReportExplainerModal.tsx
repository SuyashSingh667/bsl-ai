import React, { useState } from 'react';
import {
  Modal,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  ScrollView,
} from 'react-native';

interface Props {
  visible: boolean;
  onClose: () => void;
}

const STEPS = [
  {
    step: 1,
    icon: '⚡',
    titleEn: 'Instant Triage & Receipt',
    titleHi: 'तत्काल प्राप्ति और समीक्षा',
    descEn: 'Your report immediately registers with the Bokaro plant control room. High-priority hazards alert shift emergency teams at second zero.',
    descHi: 'आपकी रिपोर्ट तुरंत बोकारो प्लांट कंट्रोल रूम में दर्ज हो जाती है। उच्च प्राथमिकता वाले खतरों की सूचना आपातकालीन दल को तुरंत मिलती है।',
    guaranteeEn: 'Zero delay: No report is ever lost in a black hole.',
    guaranteeHi: 'शून्य देरी: कोई भी रिपोर्ट गायब नहीं होती।',
  },
  {
    step: 2,
    icon: '🛡️',
    titleEn: 'No-Blame Hazard Assessment',
    titleHi: 'बिना दोषारोपण के जोखिम मूल्यांकन',
    descEn: 'Safety engineers evaluate the physical hazard, gas line, or machine condition. The investigation focuses 100% on fixing the equipment, NOT finding fault with workers.',
    descHi: 'सुरक्षा इंजीनियर उपकरण या गैस लाइन की स्थिति का मूल्यांकन करते हैं। ध्यान केवल मशीन को ठीक करने पर होता है, कर्मचारी पर दोष मढ़ने पर नहीं।',
    guaranteeEn: 'Protected Culture: Zero discipline or penalties for reporting.',
    guaranteeHi: 'संरक्षित संस्कृति: रिपोर्ट करने पर कोई अनुशासनात्मक कार्रवाई नहीं।',
  },
  {
    step: 3,
    icon: '🛠️',
    titleEn: 'Work Order & Action Assignment',
    titleHi: 'मरम्मत कार्य आदेश और समय-सीमा',
    descEn: 'A designated maintenance supervisor or area engineer is assigned a corrective action with a mandatory completion due date.',
    descHi: 'नामित रखरखाव पर्यवेक्षक या इंजीनियर को एक निश्चित समय-सीमा के भीतर सुधार करने की जिम्मेदारी सौंपी जाती है।',
    guaranteeEn: 'Accountability: Supervisors are tracked on hazard turnaround time.',
    guaranteeHi: 'जवाबदेही: पर्यवेक्षकों की कार्य कुशलता समय पर मापी जाती है।',
  },
  {
    step: 4,
    icon: '✅',
    titleEn: 'Verified Closure & Safer Floor',
    titleHi: 'सत्यापित समाधान और सुरक्षित कार्यस्थल',
    descEn: 'Maintenance uploads proof of repair. The hazard is formally closed, and the community impact score updates to celebrate another hazard prevented.',
    descHi: 'रखरखाव दल मरम्मत का प्रमाण अपलोड करता है। खतरा स्थायी रूप से बंद हो जाता है और प्लांट सभी के लिए सुरक्षित बनता है।',
    guaranteeEn: 'Feedback Loop: You can track this full lifecycle with your code.',
    guaranteeHi: 'पारदर्शिता: आप अपने कोड से पूरी स्थिति कभी भी देख सकते हैं।',
  },
];

export const ReportExplainerModal: React.FC<Props> = ({ visible, onClose }) => {
  const [lang, setLang] = useState<'both' | 'hi' | 'en'>('both');

  return (
    <Modal visible={visible} animationType="slide" transparent>
      <View style={styles.overlay}>
        <View style={styles.container}>
          <View style={styles.header}>
            <View>
              <Text style={styles.title}>📖 What Happens to My Report?</Text>
              <Text style={styles.subtitle}>मेरी रिपोर्ट का क्या होता है? (पारदर्शिता गारंटी)</Text>
            </View>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Text style={styles.closeText}>✕</Text>
            </TouchableOpacity>
          </View>

          {/* Lang toggle chips */}
          <View style={styles.langBar}>
            <TouchableOpacity
              style={[styles.langChip, lang === 'both' && styles.langChipActive]}
              onPress={() => setLang('both')}
            >
              <Text style={[styles.langChipText, lang === 'both' && styles.langChipTextActive]}>
                Bilingual / दोनों
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.langChip, lang === 'hi' && styles.langChipActive]}
              onPress={() => setLang('hi')}
            >
              <Text style={[styles.langChipText, lang === 'hi' && styles.langChipTextActive]}>
                हिन्दी (Hindi)
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.langChip, lang === 'en' && styles.langChipActive]}
              onPress={() => setLang('en')}
            >
              <Text style={[styles.langChipText, lang === 'en' && styles.langChipTextActive]}>
                English
              </Text>
            </TouchableOpacity>
          </View>

          {/* Core Guarantee Banner */}
          <View style={styles.guaranteeBanner}>
            <Text style={styles.guaranteeIcon}>🛡️</Text>
            <View style={styles.guaranteeTextContainer}>
              <Text style={styles.guaranteeHeading}>BSL No-Blame Safety Commitment</Text>
              <Text style={styles.guaranteeSub}>
                Near-miss reporting is completely protected. We celebrate workers who identify risks early. No worker surveillance or fault-finding.
              </Text>
            </View>
          </View>

          <ScrollView style={styles.scroll}>
            {STEPS.map((s) => (
              <View key={s.step} style={styles.stepCard}>
                <View style={styles.stepHeader}>
                  <View style={styles.stepBadge}>
                    <Text style={styles.stepIcon}>{s.icon}</Text>
                    <Text style={styles.stepNumber}>Step {s.step}</Text>
                  </View>
                  <View style={styles.stepTitles}>
                    {(lang === 'both' || lang === 'en') && (
                      <Text style={styles.stepTitleEn}>{s.titleEn}</Text>
                    )}
                    {(lang === 'both' || lang === 'hi') && (
                      <Text style={styles.stepTitleHi}>{s.titleHi}</Text>
                    )}
                  </View>
                </View>

                <View style={styles.stepBody}>
                  {(lang === 'both' || lang === 'en') && (
                    <Text style={styles.stepDescEn}>{s.descEn}</Text>
                  )}
                  {(lang === 'both' || lang === 'hi') && (
                    <Text style={styles.stepDescHi}>{s.descHi}</Text>
                  )}

                  <View style={styles.stepGuarantee}>
                    <Text style={styles.guaranteePill}>
                      {(lang === 'hi') ? s.guaranteeHi : s.guaranteeEn}
                    </Text>
                  </View>
                </View>
              </View>
            ))}

            <View style={styles.footerNote}>
              <Text style={styles.footerNoteText}>
                🤝 Together, every near-miss reported prevents a serious injury tomorrow.
              </Text>
            </View>
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.85)',
    justifyContent: 'flex-end',
  },
  container: {
    backgroundColor: '#0c1524',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    maxHeight: '92%',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  title: {
    fontSize: 18,
    fontWeight: '800',
    color: '#ffffff',
  },
  subtitle: {
    fontSize: 12,
    color: '#94a3b8',
    marginTop: 2,
  },
  closeButton: {
    padding: 8,
    backgroundColor: '#1e293b',
    borderRadius: 16,
  },
  closeText: {
    color: '#ffffff',
    fontWeight: 'bold',
    fontSize: 14,
  },
  langBar: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 14,
  },
  langChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#1e293b',
    borderWidth: 1,
    borderColor: '#334155',
  },
  langChipActive: {
    backgroundColor: '#38bdf8',
    borderColor: '#38bdf8',
  },
  langChipText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#94a3b8',
  },
  langChipTextActive: {
    color: '#070d18',
  },
  guaranteeBanner: {
    flexDirection: 'row',
    backgroundColor: 'rgba(16, 185, 129, 0.12)',
    borderWidth: 1,
    borderColor: '#10b981',
    borderRadius: 12,
    padding: 12,
    alignItems: 'center',
    gap: 12,
    marginBottom: 14,
  },
  guaranteeIcon: {
    fontSize: 24,
  },
  guaranteeTextContainer: {
    flex: 1,
  },
  guaranteeHeading: {
    color: '#10b981',
    fontSize: 12,
    fontWeight: '800',
  },
  guaranteeSub: {
    color: '#cbd5e1',
    fontSize: 11,
    lineHeight: 15,
    marginTop: 2,
  },
  scroll: {
    maxHeight: 480,
  },
  stepCard: {
    backgroundColor: '#0f1d32',
    borderWidth: 1,
    borderColor: '#1e293b',
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
  },
  stepHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 8,
  },
  stepBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#1e293b',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  stepIcon: {
    fontSize: 14,
  },
  stepNumber: {
    color: '#38bdf8',
    fontSize: 11,
    fontWeight: '800',
  },
  stepTitles: {
    flex: 1,
  },
  stepTitleEn: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '800',
  },
  stepTitleHi: {
    color: '#94a3b8',
    fontSize: 12,
    fontWeight: '600',
  },
  stepBody: {
    marginTop: 4,
  },
  stepDescEn: {
    color: '#cbd5e1',
    fontSize: 12,
    lineHeight: 17,
    marginBottom: 4,
  },
  stepDescHi: {
    color: '#94a3b8',
    fontSize: 12,
    lineHeight: 17,
    marginBottom: 6,
  },
  stepGuarantee: {
    marginTop: 6,
  },
  guaranteePill: {
    color: '#38bdf8',
    fontSize: 11,
    fontWeight: '700',
  },
  footerNote: {
    alignItems: 'center',
    paddingVertical: 14,
    marginBottom: 10,
  },
  footerNoteText: {
    color: '#94a3b8',
    fontSize: 12,
    textAlign: 'center',
    fontStyle: 'italic',
  },
});
