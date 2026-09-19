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
            <Text style={styles.badgeText}>🏭 INDUSTRIAL SAFETY PLATFORM</Text>
          </View>
          {/* Outbox Status Indicator */}
          <TouchableOpacity
            style={[styles.outboxPill, pendingOutboxCount > 0 ? styles.outboxPillPending : styles.outboxPillClean]}
            onPress={handleSyncOutbox}
          >
            <Text style={styles.outboxText}>
              {isSyncingOutbox
                ? '🔄 Syncing...'
                : pendingOutboxCount > 0
                ? `🟠 ${pendingOutboxCount} Queued`
                : '🟢 Online'}
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
                <Text style={styles.langFlag}>{LANGUAGE_METADATA[code].flag}</Text>
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

      {/* Phase 6 Positive-Reinforcement Community Impact Banner (Anti-Surveillance) */}
      <View style={styles.impactBanner}>
        <View style={styles.impactHeader}>
          <Text style={styles.impactIcon}>🎉</Text>
          <View style={styles.impactTitleWrap}>
            <Text style={styles.impactTitle}>
              {cultureMetrics ? `${cultureMetrics.total_hazards_fixed} Hazards Fixed at Bokaro!` : 'Plant Safety Community'}
            </Text>
            <Text style={styles.impactSub}>
              {currentLang === 'hi'
                ? 'आपकी रिपोर्टों ने वास्तविक खतरों को हल किया और कार्यस्थल को सुरक्षित बनाया।'
                : 'Near-miss reporting makes the plant floor safer every day.'}
            </Text>
          </View>
        </View>

        {cultureMetrics && cultureMetrics.shift_participation && (
          <View style={styles.shiftBreakdown}>
            <Text style={styles.shiftLabel}>Shift Collaboration / शिफ्ट भागीदारी (No Blame):</Text>
            <View style={styles.shiftPillsRow}>
              {cultureMetrics.shift_participation.map((sp) => (
                <View key={sp.shift} style={styles.shiftPill}>
                  <Text style={styles.shiftPillName}>{sp.shift}</Text>
                  <Text style={styles.shiftPillPct}>{sp.pct}% ({sp.resolved} fixed)</Text>
                </View>
              ))}
            </View>
          </View>
        )}
      </View>

      {/* Quick Action Navigation Bar: Tracker & Process Explainer */}
      <View style={styles.toolsRow}>
        <TouchableOpacity
          style={styles.toolButton}
          onPress={() => setShowTrackerModal(true)}
        >
          <Text style={styles.toolIcon}>📍</Text>
          <View>
            <Text style={styles.toolTitle}>Track Status</Text>
            <Text style={styles.toolSub}>कोड से स्थिति जानें</Text>
          </View>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.toolButton}
          onPress={() => setShowExplainerModal(true)}
        >
          <Text style={styles.toolIcon}>📖</Text>
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
          <View style={styles.iconBadgeRed}>
            <Text style={styles.iconText}>🚨</Text>
          </View>
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
          <View style={styles.iconBadgeBlue}>
            <Text style={styles.iconText}>⚠️</Text>
          </View>
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
          <View style={styles.iconBadgePurple}>
            <Text style={styles.iconText}>🔒</Text>
          </View>
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
        <Text style={styles.kioskModeText}>🏢 Switch to Shared Kiosk / Terminal Mode</Text>
      </TouchableOpacity>

      {/* On-Screen Worker Privacy & Biometric Prohibition Consent */}
      <View style={styles.consentNoticeBox}>
        <Text style={styles.consentNoticeTitle}>🔒 Worker Data Privacy & Consent</Text>
        <Text style={styles.consentNoticeTextEn}>
          Voice recordings are processed solely for incident transcription and emergency dispatch. No biometric voice-printing or speaker profiling is performed. Retention is governed by factory safety compliance policies.
        </Text>
        <Text style={styles.consentNoticeTextHi}>
          आवाज रिकॉर्डिंग का उपयोग केवल आपातकालीन ट्रांसक्रिप्शन के लिए किया जाता है। कोई बायोमेट्रिक वॉयस-प्रिंटिंग या वक्ता पहचान नहीं की जाती है।
        </Text>
      </View>

      {/* Settings / Server Config Button */}
      <TouchableOpacity style={styles.settingsButton} onPress={onOpenSettings}>
        <Text style={styles.settingsButtonText}>⚙️ Configure Plant Server IP</Text>
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
    backgroundColor: '#070d18',
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
    marginBottom: 10,
  },
  badge: {
    backgroundColor: 'rgba(56, 189, 248, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(56, 189, 248, 0.3)',
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
    alignSelf: 'flex-start',
  },
  badgeText: {
    color: '#38bdf8',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  outboxPill: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 14,
    borderWidth: 1,
  },
  outboxPillClean: {
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
    borderColor: '#10b981',
  },
  outboxPillPending: {
    backgroundColor: 'rgba(245, 158, 11, 0.15)',
    borderColor: '#f59e0b',
  },
  outboxText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#ffffff',
  },
  title: {
    fontSize: 24,
    fontWeight: '900',
    color: '#ffffff',
    marginBottom: 4,
    letterSpacing: 0.5,
  },
  subtitle: {
    fontSize: 13,
    color: '#94a3b8',
    marginBottom: 14,
  },
  langRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 8,
  },
  langChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: '#0f172a',
    borderWidth: 1.5,
    borderColor: '#334155',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
  },
  langChipSelected: {
    borderColor: '#38bdf8',
    backgroundColor: '#1e293b',
  },
  langFlag: {
    fontSize: 14,
  },
  langText: {
    color: '#94a3b8',
    fontSize: 12,
    fontWeight: '600',
  },
  langTextSelected: {
    color: '#ffffff',
    fontWeight: '800',
  },
  dialectNoticeBox: {
    backgroundColor: 'rgba(245, 158, 11, 0.12)',
    borderWidth: 1,
    borderColor: 'rgba(245, 158, 11, 0.4)',
    borderRadius: 8,
    padding: 8,
    marginTop: 6,
  },
  dialectNoticeText: {
    color: '#fbbf24',
    fontSize: 11,
    lineHeight: 15,
  },
  impactBanner: {
    backgroundColor: 'rgba(16, 185, 129, 0.12)',
    borderWidth: 1.5,
    borderColor: '#10b981',
    borderRadius: 14,
    padding: 14,
    marginBottom: 14,
  },
  impactHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 8,
  },
  impactIcon: {
    fontSize: 26,
  },
  impactTitleWrap: {
    flex: 1,
  },
  impactTitle: {
    color: '#10b981',
    fontSize: 14,
    fontWeight: '900',
  },
  impactSub: {
    color: '#cbd5e1',
    fontSize: 11,
    lineHeight: 15,
    marginTop: 2,
  },
  shiftBreakdown: {
    marginTop: 6,
    borderTopWidth: 1,
    borderTopColor: 'rgba(16, 185, 129, 0.25)',
    paddingTop: 8,
  },
  shiftLabel: {
    color: '#a7f3d0',
    fontSize: 11,
    fontWeight: '700',
    marginBottom: 6,
  },
  shiftPillsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  shiftPill: {
    flex: 1,
    backgroundColor: 'rgba(6, 78, 59, 0.5)',
    borderRadius: 8,
    paddingVertical: 5,
    paddingHorizontal: 6,
    alignItems: 'center',
  },
  shiftPillName: {
    color: '#ffffff',
    fontSize: 10,
    fontWeight: '800',
  },
  shiftPillPct: {
    color: '#6ee7b7',
    fontSize: 10,
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
    gap: 8,
    backgroundColor: '#0f1d32',
    borderWidth: 1,
    borderColor: '#1e293b',
    borderRadius: 10,
    padding: 10,
  },
  toolIcon: {
    fontSize: 20,
  },
  toolTitle: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '800',
  },
  toolSub: {
    color: '#94a3b8',
    fontSize: 9,
    marginTop: 1,
  },
  card: {
    borderRadius: 16,
    padding: 16,
    marginBottom: 14,
    borderWidth: 1.5,
  },
  emergencyCard: {
    backgroundColor: 'rgba(239, 68, 68, 0.08)',
    borderColor: '#dc2626',
  },
  standardCard: {
    backgroundColor: 'rgba(59, 130, 246, 0.08)',
    borderColor: '#2563eb',
  },
  anonymousCard: {
    backgroundColor: 'rgba(124, 58, 237, 0.08)',
    borderColor: '#8b5cf6',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  iconBadgeRed: {
    width: 40,
    height: 40,
    borderRadius: 10,
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  iconBadgeBlue: {
    width: 40,
    height: 40,
    borderRadius: 10,
    backgroundColor: 'rgba(59, 130, 246, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  iconBadgePurple: {
    width: 40,
    height: 40,
    borderRadius: 10,
    backgroundColor: 'rgba(139, 92, 246, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  iconText: {
    fontSize: 20,
  },
  urgencyTagRed: {
    backgroundColor: '#dc2626',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  urgencyTagBlue: {
    backgroundColor: '#2563eb',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  urgencyTagPurple: {
    backgroundColor: '#7c3aed',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  urgencyText: {
    color: '#ffffff',
    fontSize: 9,
    fontWeight: '800',
  },
  cardTitle: {
    color: '#ffffff',
    fontSize: 17,
    fontWeight: '800',
    marginBottom: 4,
  },
  cardDescription: {
    color: '#cbd5e1',
    fontSize: 12,
    lineHeight: 16,
    marginBottom: 10,
  },
  actionRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  actionTextRed: {
    color: '#f87171',
    fontSize: 13,
    fontWeight: '800',
  },
  actionTextBlue: {
    color: '#60a5fa',
    fontSize: 13,
    fontWeight: '800',
  },
  shiftSelectWrap: {
    backgroundColor: '#0c1524',
    borderRadius: 8,
    padding: 8,
    marginBottom: 10,
  },
  shiftSelectLabel: {
    color: '#a5b4fc',
    fontSize: 11,
    fontWeight: '700',
    marginBottom: 6,
  },
  shiftChipsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  shiftChip: {
    flex: 1,
    backgroundColor: '#1e1b4b',
    borderWidth: 1,
    borderColor: '#4338ca',
    borderRadius: 6,
    paddingVertical: 6,
    alignItems: 'center',
  },
  shiftChipActive: {
    backgroundColor: '#7c3aed',
    borderColor: '#a78bfa',
  },
  shiftChipText: {
    color: '#c7d2fe',
    fontSize: 11,
    fontWeight: '700',
  },
  shiftChipTextActive: {
    color: '#ffffff',
    fontWeight: '800',
  },
  anonActionButton: {
    backgroundColor: '#7c3aed',
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: 'center',
  },
  anonActionText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '800',
  },
  kioskModeButton: {
    backgroundColor: '#0f172a',
    borderWidth: 1.5,
    borderColor: '#38bdf8',
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 12,
  },
  kioskModeText: {
    color: '#38bdf8',
    fontSize: 12,
    fontWeight: '800',
  },
  consentNoticeBox: {
    backgroundColor: 'rgba(15, 23, 42, 0.7)',
    borderWidth: 1,
    borderColor: 'rgba(148, 163, 184, 0.25)',
    borderRadius: 12,
    padding: 12,
    marginBottom: 14,
  },
  consentNoticeTitle: {
    color: '#e2e8f0',
    fontSize: 11,
    fontWeight: '700',
    marginBottom: 4,
    letterSpacing: 0.5,
  },
  consentNoticeTextEn: {
    color: '#94a3b8',
    fontSize: 10,
    lineHeight: 14,
    marginBottom: 4,
  },
  consentNoticeTextHi: {
    color: '#cbd5e1',
    fontSize: 10,
    lineHeight: 14,
  },
  settingsButton: {
    alignSelf: 'center',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 12,
    backgroundColor: '#1e293b',
    marginBottom: 20,
  },
  settingsButtonText: {
    color: '#94a3b8',
    fontSize: 12,
    fontWeight: '600',
  },
});
