import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';

interface ReportTypeSelectProps {
  onSelect: (type: 'emergency' | 'suspected') => void;
  onOpenSettings: () => void;
}

export const ReportTypeSelect: React.FC<ReportTypeSelectProps> = ({ onSelect, onOpenSettings }) => {
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>🏭 BOKARO STEEL PLANT</Text>
        </View>
        <Text style={styles.title}>BSL Safety Intelligence</Text>
        <Text style={styles.subtitle}>Select the nature of your report for immediate response routing.</Text>
      </View>

      {/* Emergency Alert Option */}
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
            <Text style={styles.urgencyText}>HIGH PRIORITY</Text>
          </View>
        </View>
        <Text style={styles.cardTitle}>Immediate Emergency</Text>
        <Text style={styles.cardDescription}>
          Active fire, gas leak, building collapse, or severe life hazard. Bypasses verification and immediately notifies Emergency Dispatch & Plant Fire Service.
        </Text>
        <View style={styles.actionRow}>
          <Text style={styles.actionTextRed}>Report Emergency Now ➔</Text>
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
            <Text style={styles.urgencyText}>VERIFICATION PROTOCOL</Text>
          </View>
        </View>
        <Text style={styles.cardTitle}>Report Safety Incident</Text>
        <Text style={styles.cardDescription}>
          Near miss, unusual odor, chemical leak, machine anomaly, PPE violation, or suspected hazard. Interactive AI verification will assist.
        </Text>
        <View style={styles.actionRow}>
          <Text style={styles.actionTextBlue}>Start Incident Report ➔</Text>
        </View>
      </TouchableOpacity>

      {/* Settings / Server Config Button */}
      <TouchableOpacity style={styles.settingsButton} onPress={onOpenSettings}>
        <Text style={styles.settingsButtonText}>⚙️ Configure Plant Server IP</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    justifyContent: 'center',
    backgroundColor: '#070d18',
  },
  header: {
    alignItems: 'center',
    marginBottom: 24,
  },
  badge: {
    backgroundColor: 'rgba(56, 189, 248, 0.15)',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(56, 189, 248, 0.3)',
    marginBottom: 10,
  },
  badgeText: {
    color: '#38bdf8',
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 1,
  },
  title: {
    color: '#ffffff',
    fontSize: 24,
    fontWeight: '800',
    textAlign: 'center',
    marginBottom: 6,
  },
  subtitle: {
    color: '#94a3b8',
    fontSize: 13,
    textAlign: 'center',
    paddingHorizontal: 10,
  },
  card: {
    borderRadius: 18,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1.5,
  },
  emergencyCard: {
    backgroundColor: 'rgba(239, 68, 68, 0.08)',
    borderColor: '#ef4444',
  },
  standardCard: {
    backgroundColor: 'rgba(37, 99, 235, 0.08)',
    borderColor: '#3b82f6',
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
    fontWeight: '700',
    marginBottom: 6,
  },
  cardDescription: {
    color: '#cbd5e1',
    fontSize: 13,
    lineHeight: 19,
    marginBottom: 14,
  },
  actionRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  actionTextRed: {
    color: '#f87171',
    fontSize: 14,
    fontWeight: '700',
  },
  actionTextBlue: {
    color: '#60a5fa',
    fontSize: 14,
    fontWeight: '700',
  },
  settingsButton: {
    marginTop: 10,
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
