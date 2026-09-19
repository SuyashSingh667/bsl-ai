import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View, ScrollView, Alert } from 'react-native';
import { i18n, LANGUAGE_METADATA, SupportedLanguage } from '../services/i18n';
import { outbox, OutboxItem } from '../services/outbox';
import { syncQueuedOutboxItem } from '../services/api';

interface ReportTypeSelectProps {
  onSelect: (type: 'emergency' | 'suspected') => void;
  onOpenSettings: () => void;
  onOpenKiosk: () => void;
}

export const ReportTypeSelect: React.FC<ReportTypeSelectProps> = ({
  onSelect,
  onOpenSettings,
  onOpenKiosk,
}) => {
  const [currentLang, setCurrentLang] = useState<SupportedLanguage>(i18n.getLanguage());
  const [pendingOutboxCount, setPendingOutboxCount] = useState<number>(outbox.getPendingCount());
  const [isSyncingOutbox, setIsSyncingOutbox] = useState<boolean>(false);

  useEffect(() => {
    const unsubLang = i18n.subscribe((lang) => setCurrentLang(lang));
    const unsubOutbox = outbox.subscribe((items: OutboxItem[]) => {
      setPendingOutboxCount(items.length);
    });
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
            <Text style={styles.badgeText}>🏭 BOKARO STEEL PLANT</Text>
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

      {/* Emergency Alert Option (PPE / Glove Compliant) */}
      <TouchableOpacity
        style={[styles.card, styles.emergencyCard]}
        activeOpacity={0.85}
        onPress={() => onSelect('emergency')}
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
        onPress={() => onSelect('suspected')}
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

      {/* Shared Kiosk Mode Switcher */}
      <TouchableOpacity style={styles.kioskModeButton} onPress={onOpenKiosk}>
        <Text style={styles.kioskModeText}>🏢 Switch to Shared Kiosk / Terminal Mode</Text>
      </TouchableOpacity>

      {/* Settings / Server Config Button */}
      <TouchableOpacity style={styles.settingsButton} onPress={onOpenSettings}>
        <Text style={styles.settingsButtonText}>⚙️ Configure Plant Server IP</Text>
      </TouchableOpacity>
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
    marginBottom: 20,
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
    backgroundColor: 'rgba(56, 189, 248, 0.15)',
  },
  langFlag: {
    fontSize: 13,
  },
  langText: {
    color: '#94a3b8',
    fontSize: 12,
    fontWeight: '700',
  },
  langTextSelected: {
    color: '#ffffff',
  },
  dialectNoticeBox: {
    backgroundColor: 'rgba(245, 158, 11, 0.12)',
    borderWidth: 1,
    borderColor: '#f59e0b',
    borderRadius: 8,
    padding: 8,
    marginTop: 6,
  },
  dialectNoticeText: {
    color: '#fde68a',
    fontSize: 10.5,
    lineHeight: 14,
    fontWeight: '600',
  },
  card: {
    minHeight: 120,
    borderRadius: 16,
    padding: 18,
    marginBottom: 16,
    borderWidth: 2,
    justifyContent: 'center',
  },
  emergencyCard: {
    backgroundColor: '#120708',
    borderColor: '#ef4444',
  },
  standardCard: {
    backgroundColor: '#07111e',
    borderColor: '#3b82f6',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  iconBadgeRed: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  iconBadgeBlue: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: 'rgba(59, 130, 246, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  iconText: {
    fontSize: 22,
  },
  urgencyTagRed: {
    backgroundColor: '#dc2626',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  urgencyTagBlue: {
    backgroundColor: '#2563eb',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  urgencyText: {
    color: '#ffffff',
    fontSize: 10,
    fontWeight: '800',
  },
  cardTitle: {
    color: '#ffffff',
    fontSize: 19,
    fontWeight: '800',
    marginBottom: 6,
  },
  cardDescription: {
    color: '#cbd5e1',
    fontSize: 13,
    lineHeight: 18,
    marginBottom: 12,
  },
  actionRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  actionTextRed: {
    color: '#f87171',
    fontSize: 14,
    fontWeight: '800',
  },
  actionTextBlue: {
    color: '#60a5fa',
    fontSize: 14,
    fontWeight: '800',
  },
  kioskModeButton: {
    backgroundColor: '#0f172a',
    borderWidth: 1.5,
    borderColor: '#38bdf8',
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 12,
  },
  kioskModeText: {
    color: '#38bdf8',
    fontSize: 13,
    fontWeight: '800',
  },
  settingsButton: {
    alignSelf: 'center',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 12,
    backgroundColor: '#1e293b',
  },
  settingsButtonText: {
    color: '#94a3b8',
    fontSize: 12,
    fontWeight: '600',
  },
});
