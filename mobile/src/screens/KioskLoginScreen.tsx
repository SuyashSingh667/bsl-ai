/**
 * Shared Kiosk & Supervisor Proxy Mode Screen.
 * Enables incident reporting on shared plant tablets/terminals (e.g. at blast furnace
 * control pulpits or tool cribs) without requiring every frontline worker to own a smartphone.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ScrollView,
  Alert,
} from 'react-native';

export interface KioskSession {
  reportingMode: 'kiosk' | 'supervisor_proxy' | 'personal';
  workerBadgeId: string;
  supervisorId?: string;
  kioskStationId: string;
}

interface Props {
  onSessionStart: (session: KioskSession) => void;
  onExitKiosk: () => void;
  stationId?: string;
}

export const KioskLoginScreen: React.FC<Props> = ({
  onSessionStart,
  onExitKiosk,
  stationId = 'KSK-BF1-02 (Blast Furnace 1)',
}) => {
  const [badgeId, setBadgeId] = useState('');
  const [isSupervisorProxy, setIsSupervisorProxy] = useState(false);
  const [supervisorId, setSupervisorId] = useState('');

  const quickBadges = [
    { id: 'SAIL-5524', role: 'Casthouse Tapper (Shift B)' },
    { id: 'SAIL-4102', role: 'SMS-II Crane Operator' },
    { id: 'SAIL-6391', role: 'Gas Safety Marshall' },
  ];

  const handleStart = () => {
    const finalBadge = badgeId.trim();
    if (!finalBadge) {
      Alert.alert('Badge ID Required', 'Please enter or select a worker badge ID to proceed.');
      return;
    }

    if (isSupervisorProxy && !supervisorId.trim()) {
      Alert.alert('Supervisor ID Required', 'Please enter your Supervisor Badge ID for proxy reporting.');
      return;
    }

    onSessionStart({
      reportingMode: isSupervisorProxy ? 'supervisor_proxy' : 'kiosk',
      workerBadgeId: finalBadge,
      supervisorId: isSupervisorProxy ? supervisorId.trim() : undefined,
      kioskStationId: stationId,
    });
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      {/* Kiosk Station Header */}
      <View style={styles.stationBadge}>
        <Text style={styles.stationIcon}>🏢</Text>
        <View>
          <Text style={styles.stationLabel}>SHARED PLANT TERMINAL</Text>
          <Text style={styles.stationTitle}>{stationId}</Text>
        </View>
      </View>

      <Text style={styles.title}>Worker Identification</Text>
      <Text style={styles.subtitle}>
        Identify yourself using your Bokaro Steel badge or employee PIN to begin reporting.
      </Text>

      {/* Badge Input */}
      <View style={styles.inputContainer}>
        <Text style={styles.inputLabel}>WORKER BADGE / EMPLOYEE ID:</Text>
        <TextInput
          style={styles.textInput}
          placeholder="e.g. SAIL-5524 or 4-digit PIN"
          placeholderTextColor="#64748b"
          value={badgeId}
          onChangeText={setBadgeId}
          autoCapitalize="characters"
        />
      </View>

      {/* Quick Badge Presets */}
      <Text style={styles.quickLabel}>QUICK IDENTIFICATION PRESETS:</Text>
      <View style={styles.quickGrid}>
        {quickBadges.map((b) => (
          <TouchableOpacity
            key={b.id}
            style={[styles.quickCard, badgeId === b.id && styles.quickCardSelected]}
            onPress={() => setBadgeId(b.id)}
          >
            <Text style={styles.quickId}>{b.id}</Text>
            <Text style={styles.quickRole}>{b.role}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Supervisor Proxy Toggle */}
      <TouchableOpacity
        style={[styles.proxyToggleCard, isSupervisorProxy && styles.proxyToggleCardActive]}
        onPress={() => setIsSupervisorProxy(!isSupervisorProxy)}
      >
        <View style={styles.checkbox}>
          <Text style={styles.checkboxCheck}>{isSupervisorProxy ? '✓' : ''}</Text>
        </View>
        <View style={styles.proxyTextWrap}>
          <Text style={styles.proxyTitle}>Supervisor Reporting on Behalf of Worker</Text>
          <Text style={styles.proxySub}>
            Enable this if you are a shift supervisor logging an incident witnessed by a crew member.
          </Text>
        </View>
      </TouchableOpacity>

      {isSupervisorProxy && (
        <View style={styles.inputContainer}>
          <Text style={styles.inputLabel}>SUPERVISOR BADGE ID:</Text>
          <TextInput
            style={styles.textInput}
            placeholder="e.g. SUP-8821 (Shift Supervisor)"
            placeholderTextColor="#64748b"
            value={supervisorId}
            onChangeText={setSupervisorId}
            autoCapitalize="characters"
          />
        </View>
      )}

      {/* Start Button (Glove/PPE Friendly) */}
      <TouchableOpacity style={styles.startButton} onPress={handleStart}>
        <Text style={styles.startButtonText}>Begin Incident Report ➔</Text>
      </TouchableOpacity>

      {/* Exit Kiosk Button */}
      <TouchableOpacity style={styles.exitButton} onPress={onExitKiosk}>
        <Text style={styles.exitButtonText}>Switch to Personal Device Mode</Text>
      </TouchableOpacity>
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
  stationBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1c1c1e',
    borderWidth: 1,
    borderColor: 'rgba(10, 132, 255, 0.3)',
    padding: 16,
    borderRadius: 20,
    marginBottom: 20,
    gap: 12,
  },
  stationIcon: {
    fontSize: 28,
  },
  stationLabel: {
    color: '#0A84FF',
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.2,
  },
  stationTitle: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '600',
  },
  title: {
    fontSize: 26,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: 6,
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: 14,
    color: 'rgba(235, 235, 245, 0.65)',
    lineHeight: 20,
    marginBottom: 20,
    letterSpacing: -0.1,
  },
  inputContainer: {
    marginBottom: 16,
  },
  inputLabel: {
    color: 'rgba(235, 235, 245, 0.45)',
    fontSize: 11,
    fontWeight: '600',
    marginBottom: 6,
    letterSpacing: 0.2,
  },
  textInput: {
    backgroundColor: '#1c1c1e',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.15)',
    borderRadius: 16,
    color: '#ffffff',
    fontSize: 16,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontWeight: '500',
  },
  quickLabel: {
    color: 'rgba(235, 235, 245, 0.45)',
    fontSize: 11,
    fontWeight: '600',
    marginBottom: 8,
    letterSpacing: 0.2,
  },
  quickGrid: {
    gap: 8,
    marginBottom: 20,
  },
  quickCard: {
    backgroundColor: '#1c1c1e',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
    padding: 14,
    borderRadius: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  quickCardSelected: {
    borderColor: '#0A84FF',
    backgroundColor: 'rgba(10, 132, 255, 0.15)',
  },
  quickId: {
    color: '#ffffff',
    fontWeight: '600',
    fontSize: 14,
  },
  quickRole: {
    color: 'rgba(235, 235, 245, 0.55)',
    fontSize: 12,
  },
  proxyToggleCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1c1c1e',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
    padding: 16,
    borderRadius: 18,
    marginBottom: 16,
  },
  proxyToggleCardActive: {
    borderColor: '#FF9F0A',
    backgroundColor: 'rgba(255, 159, 10, 0.12)',
  },
  checkbox: {
    width: 26,
    height: 26,
    borderRadius: 8,
    borderWidth: 1.5,
    borderColor: '#FF9F0A',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
    backgroundColor: 'transparent',
  },
  checkboxCheck: {
    color: '#FF9F0A',
    fontWeight: '900',
    fontSize: 16,
  },
  proxyTextWrap: {
    flex: 1,
  },
  proxyTitle: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
  proxySub: {
    color: 'rgba(235, 235, 245, 0.65)',
    fontSize: 12,
    lineHeight: 16,
    marginTop: 2,
  },
  startButton: {
    backgroundColor: '#30D158',
    minHeight: 52,
    borderRadius: 9999,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  startButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
    letterSpacing: -0.2,
  },
  exitButton: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  exitButtonText: {
    color: '#0A84FF',
    fontSize: 14,
    fontWeight: '500',
  },
});
