import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View, ScrollView, Alert } from 'react-native';
import { i18n, LANGUAGE_METADATA, SupportedLanguage } from '../services/i18n';
import { outbox, OutboxItem } from '../services/outbox';
import { syncQueuedOutboxItem, getCultureMetrics, CultureMetricsData } from '../services/api';
import { ReportStatusTrackerModal } from '../components/ReportStatusTrackerModal';
import { ReportExplainerModal } from '../components/ReportExplainerModal';

interface ReportTypeSelectProps {
  onSelect: (type: 'emergency' | 'suspected', isAnonymous?: boolean, shift?: string) => void;
  onOpenSettings: () => void;
  onOpenKiosk: () => void;
}

const SHIFT_OPTIONS = ['Shift A', 'Shift B', 'Shift C'];

export const ReportTypeSelect: React.FC<ReportTypeSelectProps> = ({
  onSelect,
  onOpenSettings,
  onOpenKiosk,
}) => {
  const [currentLang, setCurrentLang] = useState<SupportedLanguage>(i18n.getLanguage());
  const [pendingOutboxCount, setPendingOutboxCount] = useState<number>(outbox.getPendingCount());
  const [isSyncingOutbox, setIsSyncingOutbox] = useState<boolean>(false);

  // Phase 6 Culture & Transparency state
  const [showTrackerModal, setShowTrackerModal] = useState<boolean>(false);
  const [showExplainerModal, setShowExplainerModal] = useState<boolean>(false);
  const [cultureMetrics, setCultureMetrics] = useState<CultureMetricsData | null>(null);
  const [selectedShift, setSelectedShift] = useState<string>('Shift A');

  useEffect(() => {
    const unsubLang = i18n.subscribe((lang) => setCurrentLang(lang));
    const unsubOutbox = outbox.subscribe((items: OutboxItem[]) => {
      setPendingOutboxCount(items.length);
    });

    // Load positive reinforcement metrics (team participation only, zero worker surveillance)
    getCultureMetrics('bsl_bokaro')
      .then((data) => setCultureMetrics(data))
      .catch((err) => console.log('Culture metrics fallback:', err));

    return () => {
      unsubLang();
      unsubOutbox();
    };
  }, []);

  const handleSyncOutbox = async () => {
    if (pendingOutboxCount === 0) {
      Alert.alert('Outbox Empty', 'All incident reports and voice notes have synced with the Bokaro plant server.');
      return;
    }
    setIsSyncingOutbox(true);
    const result = await outbox.syncOutbox(async (item) => {
      return await syncQueuedOutboxItem(item);
    });
    setIsSyncingOutbox(false);
    Alert.alert('Outbox Sync Complete', `Synced ${result.synced} items. Remaining offline: ${result.remaining}`);
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <View style={styles.headerTopRow}>
          <View style={styles.badge}>
            <Text style={styles.badgeText}>INDUSTRIAL SAFETY PLATFORM</Text>
          </View>
          {/* Outbox Status Indicator */}
          <TouchableOpacity
            style={[styles.outboxPill, pendingOutboxCount > 0 ? styles.outboxPillPending : styles.outboxPillClean]}
            onPress={handleSyncOutbox}
          >
            <Text style={styles.outboxText}>
              {isSyncingOutbox
                ? 'Syncing...'
                : pendingOutboxCount > 0
                ? `${pendingOutboxCount} Queued`
                : 'Online'}
            </Text>
          </TouchableOpacity>
        </View>

        <Text style={styles.title}>{i18n.t('appTitle')}</Text>
        <Text style={styles.subtitle}>{i18n.t('appSubtitle')}</Text>

        {/* Language Selection Chips */}
        <View style={styles.langRow}>
          {(Object.keys(LANGUAGE_METADATA) as SupportedLanguage[]).map((code) => {
            const isSelected = currentLang === code;
            return (
              <TouchableOpacity
                key={code}
                style={[styles.langChip, isSelected && styles.langChipSelected]}
                onPress={() => i18n.setLanguage(code)}
              >
                <Text style={[styles.langText, isSelected && styles.langTextSelected]}>
                  {LANGUAGE_METADATA[code].nativeName}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>

        {/* Dialect Disclaimer for Regional Languages */}
        {(currentLang === 'bn' || currentLang === 'or') && (
          <View style={styles.dialectNoticeBox}>
            <Text style={styles.dialectNoticeText}>{i18n.t('dialectNotice')}</Text>
          </View>
        )}
      </View>

      {/* Quick Action Navigation Bar: Tracker & Process Explainer */}
      <View style={styles.toolsRow}>
        <TouchableOpacity
          style={styles.toolButton}
          onPress={() => setShowTrackerModal(true)}
        >
          <View>
            <Text style={styles.toolTitle}>Track Status</Text>
            <Text style={styles.toolSub}>कोड से स्थिति जानें</Text>
          </View>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.toolButton}
          onPress={() => setShowExplainerModal(true)}
        >
          <View>
            <Text style={styles.toolTitle}>Report Lifecycle</Text>
            <Text style={styles.toolSub}>मेरी रिपोर्ट का क्या होता है?</Text>
          </View>
        </TouchableOpacity>
      </View>

      {/* Emergency Alert Option (PPE / Glove Compliant) */}
      <TouchableOpacity
        style={[styles.card, styles.emergencyCard]}
        activeOpacity={0.85}
        onPress={() => onSelect('emergency', false, selectedShift)}
      >
        <View style={styles.cardHeader}>
          <View style={styles.urgencyTagRed}>
            <Text style={styles.urgencyText}>HIGH PRIORITY (FAST-PATH)</Text>
          </View>
        </View>
        <Text style={styles.cardTitle}>{i18n.t('emergencyButton')}</Text>
        <Text style={styles.cardDescription}>{i18n.t('emergencyDesc')}</Text>
        <View style={styles.actionRow}>
          <Text style={styles.actionTextRed}>Report Critical Emergency Now ➔</Text>
        </View>
      </TouchableOpacity>

      {/* Standard Incident Option */}
      <TouchableOpacity
        style={[styles.card, styles.standardCard]}
        activeOpacity={0.85}
        onPress={() => onSelect('suspected', false, selectedShift)}
      >
        <View style={styles.cardHeader}>
          <View style={styles.urgencyTagBlue}>
            <Text style={styles.urgencyText}>STANDARD REPORT</Text>
          </View>
        </View>
        <Text style={styles.cardTitle}>{i18n.t('suspectedButton')}</Text>
        <Text style={styles.cardDescription}>{i18n.t('suspectedDesc')}</Text>
        <View style={styles.actionRow}>
          <Text style={styles.actionTextBlue}>Start Observation Report ➔</Text>
        </View>
      </TouchableOpacity>

      {/* Phase 6: Anonymous No-Blame Near-Miss Card */}
      <View style={[styles.card, styles.anonymousCard]}>
        <View style={styles.cardHeader}>
          <View style={styles.urgencyTagPurple}>
            <Text style={styles.urgencyText}>ANONYMOUS / NO-BLAME</Text>
          </View>
        </View>
        <Text style={styles.cardTitle}>Anonymous Near-Miss / गुप्त रिपोर्ट</Text>
        <Text style={styles.cardDescription}>
          Report close calls and hazards completely anonymously. Attributed ONLY to your zone and shift. Your identity and phone are strictly unrecorded.
        </Text>

        {/* Shift selector for anonymous reporting */}
        <View style={styles.shiftSelectWrap}>
          <Text style={styles.shiftSelectLabel}>Attribute to Shift / कार्य पाली:</Text>
          <View style={styles.shiftChipsRow}>
            {SHIFT_OPTIONS.map((sh) => (
              <TouchableOpacity
                key={sh}
                style={[styles.shiftChip, selectedShift === sh && styles.shiftChipActive]}
                onPress={() => setSelectedShift(sh)}
              >
                <Text style={[styles.shiftChipText, selectedShift === sh && styles.shiftChipTextActive]}>
                  {sh}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <TouchableOpacity
          style={styles.anonActionButton}
          activeOpacity={0.85}
          onPress={() => onSelect('suspected', true, selectedShift)}
        >
          <Text style={styles.anonActionText}>Submit Protected Near-Miss ➔</Text>
        </TouchableOpacity>
      </View>

      {/* Shared Kiosk Mode Switcher */}
      <TouchableOpacity style={styles.kioskModeButton} onPress={onOpenKiosk}>
        <Text style={styles.kioskModeText}>Switch to Shared Kiosk / Terminal Mode</Text>
      </TouchableOpacity>

      {/* On-Screen Worker Privacy & Biometric Prohibition Consent */}
      <View style={styles.consentNoticeBox}>
        <Text style={styles.consentNoticeTitle}>Worker Data Privacy & Consent</Text>
        <Text style={styles.consentNoticeTextEn}>
          Voice recordings are processed solely for incident transcription and emergency dispatch. No biometric voice-printing or speaker profiling is performed. Retention is governed by factory safety compliance policies.
        </Text>
        <Text style={styles.consentNoticeTextHi}>
          आवाज रिकॉर्डिंग का उपयोग केवल आपातकालीन ट्रांसक्रिप्शन के लिए किया जाता है। कोई बायोमेट्रिक वॉयस-प्रिंटिंग या वक्ता पहचान नहीं की जाती है।
        </Text>
      </View>

      {/* Settings / Server Config Button */}
      <TouchableOpacity style={styles.settingsButton} onPress={onOpenSettings}>
        <Text style={styles.settingsButtonText}>Configure Plant Server IP</Text>
      </TouchableOpacity>

      {/* Modals */}
      <ReportStatusTrackerModal
        visible={showTrackerModal}
        onClose={() => setShowTrackerModal(false)}
      />
      <ReportExplainerModal
        visible={showExplainerModal}
        onClose={() => setShowExplainerModal(false)}
      />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 20,
    backgroundColor: '#000000',
    flexGrow: 1,
    justifyContent: 'center',
  },
  header: {
    marginBottom: 16,
  },
  headerTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  badge: {
    backgroundColor: 'rgba(255, 255, 255, 0.06)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 9999,
    paddingHorizontal: 12,
    paddingVertical: 5,
    alignSelf: 'flex-start',
  },
  badgeText: {
    color: 'rgba(235, 235, 245, 0.7)',
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.2,
  },
  outboxPill: {
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 9999,
    borderWidth: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.06)',
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  outboxPillClean: {
    backgroundColor: 'rgba(255, 255, 255, 0.06)',
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  outboxPillPending: {
    backgroundColor: 'rgba(255, 255, 255, 0.06)',
    borderColor: 'rgba(255, 255, 255, 0.15)',
  },
  outboxText: {
    fontSize: 12,
    fontWeight: '600',
    color: 'rgba(235, 235, 245, 0.75)',
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: 6,
    letterSpacing: -0.6,
  },
  subtitle: {
    fontSize: 14,
    color: 'rgba(235, 235, 245, 0.6)',
    marginBottom: 16,
    lineHeight: 20,
    letterSpacing: -0.2,
  },
  langRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 8,
  },
  langChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#1c1c1e',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 9999,
  },
  langChipSelected: {
    borderColor: '#ffffff',
    backgroundColor: '#2c2c2e',
  },
  langFlag: {
    fontSize: 14,
  },
  langText: {
    color: 'rgba(235, 235, 245, 0.6)',
    fontSize: 13,
    fontWeight: '500',
    letterSpacing: -0.1,
  },
  langTextSelected: {
    color: '#ffffff',
    fontWeight: '600',
  },
  dialectNoticeBox: {
    backgroundColor: '#1c1c1e',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 16,
    padding: 10,
    marginTop: 6,
  },
  dialectNoticeText: {
    color: 'rgba(235, 235, 245, 0.65)',
    fontSize: 12,
    lineHeight: 16,
    fontWeight: '500',
  },
  toolsRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 14,
  },
  toolButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: '#1c1c1e',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 16,
    padding: 12,
  },
  toolIcon: {
    fontSize: 20,
  },
  toolTitle: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '600',
    letterSpacing: -0.2,
  },
  toolSub: {
    color: 'rgba(235, 235, 245, 0.45)',
    fontSize: 10,
    marginTop: 2,
  },
  card: {
    backgroundColor: '#1c1c1e',
    borderRadius: 22,
    padding: 18,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  emergencyCard: {
    backgroundColor: '#1c1c1e',
    borderColor: 'rgba(255, 255, 255, 0.12)',
  },
  standardCard: {
    backgroundColor: '#1c1c1e',
    borderColor: 'rgba(255, 255, 255, 0.12)',
  },
  anonymousCard: {
    backgroundColor: '#1c1c1e',
    borderColor: 'rgba(255, 255, 255, 0.12)',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  iconBadgeRed: {
    width: 44,
    height: 44,
    borderRadius: 14,
    backgroundColor: '#2c2c2e',
    justifyContent: 'center',
    alignItems: 'center',
  },
  iconBadgeBlue: {
    width: 44,
    height: 44,
    borderRadius: 14,
    backgroundColor: '#2c2c2e',
    justifyContent: 'center',
    alignItems: 'center',
  },
  iconBadgePurple: {
    width: 44,
    height: 44,
    borderRadius: 14,
    backgroundColor: '#2c2c2e',
    justifyContent: 'center',
    alignItems: 'center',
  },
  iconText: {
    fontSize: 22,
  },
  urgencyTagRed: {
    backgroundColor: '#2c2c2e',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 9999,
  },
  urgencyTagBlue: {
    backgroundColor: '#2c2c2e',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 9999,
  },
  urgencyTagPurple: {
    backgroundColor: '#2c2c2e',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 9999,
  },
  urgencyText: {
    color: 'rgba(235, 235, 245, 0.75)',
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.2,
  },
  cardTitle: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 4,
    letterSpacing: -0.3,
  },
  cardDescription: {
    color: 'rgba(235, 235, 245, 0.6)',
    fontSize: 13,
    lineHeight: 18,
    marginBottom: 12,
  },
  actionRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  actionTextRed: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: -0.2,
  },
  actionTextBlue: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: -0.2,
  },
  shiftSelectWrap: {
    backgroundColor: '#161618',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    padding: 10,
    marginBottom: 12,
  },
  shiftSelectLabel: {
    color: 'rgba(235, 235, 245, 0.55)',
    fontSize: 11,
    fontWeight: '600',
    marginBottom: 6,
  },
  shiftChipsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  shiftChip: {
    flex: 1,
    backgroundColor: '#2c2c2e',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 9999,
    paddingVertical: 8,
    alignItems: 'center',
  },
  shiftChipActive: {
    backgroundColor: '#ffffff',
    borderColor: '#ffffff',
  },
  shiftChipText: {
    color: 'rgba(235, 235, 245, 0.65)',
    fontSize: 12,
    fontWeight: '600',
  },
  shiftChipTextActive: {
    color: '#000000',
    fontWeight: '700',
  },
  anonActionButton: {
    backgroundColor: '#ffffff',
    borderRadius: 9999,
    paddingVertical: 14,
    alignItems: 'center',
  },
  anonActionText: {
    color: '#000000',
    fontSize: 15,
    fontWeight: '600',
    letterSpacing: -0.2,
  },
  kioskModeButton: {
    backgroundColor: '#1c1c1e',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
    paddingVertical: 14,
    borderRadius: 9999,
    alignItems: 'center',
    marginBottom: 12,
  },
  kioskModeText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: -0.2,
  },
  consentNoticeBox: {
    backgroundColor: '#1c1c1e',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 16,
    padding: 14,
    marginBottom: 16,
  },
  consentNoticeTitle: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 4,
    letterSpacing: -0.2,
  },
  consentNoticeTextEn: {
    color: 'rgba(235, 235, 245, 0.6)',
    fontSize: 11,
    lineHeight: 15,
    marginBottom: 4,
  },
  consentNoticeTextHi: {
    color: 'rgba(235, 235, 245, 0.45)',
    fontSize: 11,
    lineHeight: 15,
  },
  settingsButton: {
    alignSelf: 'center',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 9999,
    backgroundColor: '#1c1c1e',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
    marginBottom: 24,
  },
  settingsButtonText: {
    color: 'rgba(235, 235, 245, 0.6)',
    fontSize: 13,
    fontWeight: '500',
  },
});
