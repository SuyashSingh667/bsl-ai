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
    backgroundColor: '#1c1c1e',
    borderWidth: 1,
    borderColor: 'rgba(255, 69, 58, 0.4)',
    borderRadius: 18,
    padding: 14,
    marginVertical: 12,
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
    color: '#FF453A',
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.2,
  },
  headerSub: {
    color: 'rgba(235, 235, 245, 0.7)',
    fontSize: 12,
    lineHeight: 16,
    marginTop: 2,
  },
  alternativeBox: {
    backgroundColor: '#000000',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    padding: 10,
    marginTop: 6,
  },
  altLabel: {
    color: '#0A84FF',
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.2,
    marginBottom: 2,
  },
  altText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '500',
    lineHeight: 16,
  },
  kioskButton: {
    backgroundColor: '#2c2c2e',
    borderWidth: 1,
    borderColor: 'rgba(10, 132, 255, 0.4)',
    borderRadius: 9999,
    paddingVertical: 10,
    alignItems: 'center',
    marginTop: 10,
  },
  kioskButtonText: {
    color: '#0A84FF',
    fontSize: 13,
    fontWeight: '600',
  },
});
