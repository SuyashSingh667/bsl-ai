/**
 * Zone Restriction & Intrinsically-Safe Area Banner.
 * Displays when a worker selects or is located in an explosive gas or hazardous
 * zone where commercial smartphones are prohibited under SAIL-BSL safety regulations.
 * Directs workers to explosion-proof fixed kiosks or emergency intercoms.
 */

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Linking } from 'react-native';

interface Props {
  zoneId?: string;
  zoneName?: string;
  safeAlternative?: string;
  onUseKiosk?: () => void;
}

export const RESTRICTED_ZONES_MAP: Record<string, { name: string; alternative: string }> = {
  BF1: {
    name: 'Blast Furnace 1',
    alternative: 'Use Explosion-Proof Kiosk Station KSK-BF1-02 (Casthouse North Control Cabin) or Emergency Intercom at Assembly Point B',
  },
  BF2: {
    name: 'Blast Furnace 2',
    alternative: 'Use Explosion-Proof Kiosk Station KSK-BF2-01 (BF-2 Shift Office) or Emergency Intercom at Assembly Point C',
  },
  COB: {
    name: 'Coke Oven Battery & By-Product Plant',
    alternative: 'Use Gas Marshall Kiosk Station KSK-COB-01 or Intercom at Battery Control Pulpit',
  },
  GHS: {
    name: 'Gas Holder Station',
    alternative: 'Use Intrinsically-Safe Intercom at GHS Security Gate or Kiosk KSK-GHS-01',
  },
  SMS: {
    name: 'Steel Melting Shop / LD Converters',
    alternative: 'Use Fixed Kiosk KSK-SMS-04 (Converter Pulpit) or Crane Bay Intercom',
  },
  CC: {
    name: 'Continuous Casting',
    alternative: 'Use Fixed Kiosk KSK-CC-02 (Caster Control Room) or Assembly Point E Intercom',
  },
};

export const ZoneRestrictionBanner: React.FC<Props> = ({
  zoneId,
  zoneName,
  safeAlternative,
  onUseKiosk,
}) => {
  if (!zoneId) return null;

  const info = RESTRICTED_ZONES_MAP[zoneId.toUpperCase()];
  if (!info) return null;

  const finalAlt = safeAlternative || info.alternative;

  return (
    <View style={styles.bannerContainer}>
      <View style={styles.headerRow}>
        <Text style={styles.warningIcon}>⛔</Text>
        <View style={styles.headerTextWrap}>
          <Text style={styles.headerTitle}>PHONE-RESTRICTED / INTRINSICALLY SAFE ZONE</Text>
          <Text style={styles.headerSub}>
            Commercial smartphones prohibited in {info.name} ({zoneId}) due to explosive gas atmosphere (CO/BF Gas).
          </Text>
        </View>
      </View>

      <View style={styles.alternativeBox}>
        <Text style={styles.altLabel}>SAFE REPORTING ALTERNATIVE:</Text>
        <Text style={styles.altText}>📍 {finalAlt}</Text>
      </View>

      {onUseKiosk && (
        <TouchableOpacity style={styles.kioskButton} onPress={onUseKiosk}>
          <Text style={styles.kioskButtonText}>Switch to Fixed Kiosk Mode ➔</Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  bannerContainer: {
    backgroundColor: 'rgba(239, 68, 68, 0.12)',
    borderWidth: 1.5,
    borderColor: '#ef4444',
    borderRadius: 10,
    padding: 12,
    marginVertical: 10,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    marginBottom: 8,
  },
  warningIcon: {
    fontSize: 22,
  },
  headerTextWrap: {
    flex: 1,
  },
  headerTitle: {
    color: '#f87171',
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 0.5,
  },
  headerSub: {
    color: '#fca5a5',
    fontSize: 11,
    lineHeight: 15,
    marginTop: 2,
  },
  alternativeBox: {
    backgroundColor: '#0f172a',
    borderWidth: 1,
    borderColor: '#334155',
    borderRadius: 6,
    padding: 8,
    marginTop: 4,
  },
  altLabel: {
    color: '#38bdf8',
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  altText: {
    color: '#f1f5f9',
    fontSize: 11,
    fontWeight: '600',
    lineHeight: 15,
  },
  kioskButton: {
    backgroundColor: '#1e293b',
    borderWidth: 1,
    borderColor: '#38bdf8',
    borderRadius: 6,
    paddingVertical: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  kioskButtonText: {
    color: '#38bdf8',
    fontSize: 11,
    fontWeight: '700',
  },
});
