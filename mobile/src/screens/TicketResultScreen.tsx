import React from 'react';
import {
  Image,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { StepIndicator } from '../components/StepIndicator';
import { Ticket } from '../services/api';
import { getApiBaseUrl } from '../services/config';

interface TicketResultScreenProps {
  ticket: Ticket;
  onStartNewReport: () => void;
}

export const TicketResultScreen: React.FC<TicketResultScreenProps> = ({
  ticket,
  onStartNewReport,
}) => {
  const [fullPhotoUrl, setFullPhotoUrl] = React.useState<string | null>(null);
  const report = ticket.safety_report;
  const verifiedSummary = report?.verified_summary;
  const threatLevel = report?.threat_level || 'HIGH PRIORITY';
  const recipients = report?.recipients || [];

  React.useEffect(() => {
    const resolvePhoto = async () => {
      const p = ticket.photo_url || (ticket.photo_proof_path ? `/photos/${ticket.photo_proof_path.split('/').pop()}` : null);
      if (p) {
        if (p.startsWith('http')) {
          setFullPhotoUrl(p);
        } else {
          const base = await getApiBaseUrl();
          setFullPhotoUrl(`${base}${p}`);
        }
      }
    };
    resolvePhoto();
  }, [ticket]);

  return (
    <View style={styles.container}>
      <StepIndicator currentStep={5} />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Success Header */}
        <View style={styles.successBanner}>
          <Text style={styles.successIcon}>✅</Text>
          <Text style={styles.successTitle}>Incident Logged & Dispatched</Text>
          <Text style={styles.ticketIdText}>Ticket ID: {ticket.id}</Text>
        </View>

        {/* Threat Level Badge */}
        <View style={styles.badgeContainer}>
          <View style={styles.threatBadge}>
            <Text style={styles.threatBadgeText}>{threatLevel}</Text>
          </View>
          <View style={styles.categoryBadge}>
            <Text style={styles.categoryBadgeText}>
              {ticket.predicted_category?.replace('_', ' ').toUpperCase()}
            </Text>
          </View>
        </View>

        {/* Narrative / Executive summary */}
        {report?.situation_narrative && (
          <View style={styles.card}>
            <Text style={styles.cardHeader}>Risk & Incident Assessment</Text>
            <Text style={styles.narrativeText}>{report.situation_narrative}</Text>
          </View>
        )}

        {/* Verified Facts Matrix */}
        <View style={styles.card}>
          <Text style={styles.cardHeader}>Verified Safety Facts</Text>
          <View style={styles.factRow}>
            <Text style={styles.factLabel}>Visual Confirmation:</Text>
            <Text style={styles.factValue}>
              {verifiedSummary?.observation_mode || 'Direct Observation'}
            </Text>
          </View>
          <View style={styles.factRow}>
            <Text style={styles.factLabel}>Hazard Activity:</Text>
            <Text style={styles.factValue}>{verifiedSummary?.active_state || 'Active'}</Text>
          </View>
          <View style={styles.factRow}>
            <Text style={styles.factLabel}>Equipment / Origin:</Text>
            <Text style={styles.factValue}>
              {verifiedSummary?.equipment || 'General Facility'}
            </Text>
          </View>
          <View style={styles.factRow}>
            <Text style={styles.factLabel}>Exposed Personnel:</Text>
            <Text style={styles.factValue}>
              {verifiedSummary?.exposed_personnel || 'Unspecified'}
            </Text>
          </View>
          <View style={styles.factRow}>
            <Text style={styles.factLabel}>Calculated Risk Score:</Text>
            <Text style={styles.factValue}>{ticket.risk_score || '0.75'}</Text>
          </View>
        </View>

        {/* Attached Photo Proof */}
        {fullPhotoUrl && (
          <View style={styles.card}>
            <Text style={styles.cardHeader}>Field Photographic Proof</Text>
            <Image
              source={{ uri: fullPhotoUrl }}
              style={styles.photoProofImage}
              resizeMode="cover"
            />
          </View>
        )}

        {/* Dispatched Recipients */}
        {recipients.length > 0 && (
          <View style={styles.card}>
            <Text style={styles.cardHeader}>Designated Emergency Dispatches</Text>
            {recipients.map((r: any, idx: number) => (
              <View key={idx} style={styles.recipientRow}>
                <View style={styles.recipientDot} />
                <View style={styles.recipientInfo}>
                  <Text style={styles.recipientDept}>{r.department}</Text>
                  <Text style={styles.recipientSub}>
                    {r.role} • Contact: {r.contact} • {r.status}
                  </Text>
                </View>
              </View>
            ))}
          </View>
        )}

        {/* Reset / New Report Button */}
        <TouchableOpacity style={styles.newReportButton} onPress={onStartNewReport}>
          <Text style={styles.newReportButtonText}>Log Another Safety Report ➔</Text>
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
  successBanner: {
    alignItems: 'center',
    marginBottom: 16,
  },
  successIcon: {
    fontSize: 40,
    marginBottom: 6,
  },
  successTitle: {
    color: '#ffffff',
    fontSize: 20,
    fontWeight: '800',
    marginBottom: 4,
  },
  ticketIdText: {
    color: '#38bdf8',
    fontSize: 13,
    fontWeight: '700',
    letterSpacing: 1,
  },
  badgeContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 8,
    marginBottom: 20,
  },
  threatBadge: {
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ef4444',
  },
  threatBadgeText: {
    color: '#f87171',
    fontSize: 11,
    fontWeight: '800',
  },
  categoryBadge: {
    backgroundColor: 'rgba(37, 99, 235, 0.2)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#3b82f6',
  },
  categoryBadgeText: {
    color: '#60a5fa',
    fontSize: 11,
    fontWeight: '800',
  },
  card: {
    backgroundColor: '#0f172a',
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1e293b',
    marginBottom: 16,
  },
  cardHeader: {
    color: '#38bdf8',
    fontSize: 13,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  narrativeText: {
    color: '#cbd5e1',
    fontSize: 14,
    lineHeight: 20,
  },
  factRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
  },
  factLabel: {
    color: '#94a3b8',
    fontSize: 13,
  },
  factValue: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '600',
    flex: 1,
    textAlign: 'right',
  },
  photoProofImage: {
    width: '100%',
    height: 200,
    borderRadius: 8,
  },
  recipientRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 6,
  },
  recipientDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#34d399',
    marginRight: 10,
  },
  recipientInfo: {
    flex: 1,
  },
  recipientDept: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '700',
  },
  recipientSub: {
    color: '#64748b',
    fontSize: 11,
  },
  newReportButton: {
    backgroundColor: '#2563eb',
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 10,
  },
  newReportButtonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '700',
  },
});
