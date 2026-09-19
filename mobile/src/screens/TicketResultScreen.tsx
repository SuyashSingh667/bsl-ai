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
  const visualAnalysis = ticket.visual_analysis || report?.visual_analysis;

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

        {/* Safety-Critical AI Advisory Notice */}
        <View style={styles.aiNoticeBanner}>
          <Text style={styles.aiNoticeIcon}>⚠️</Text>
          <View style={styles.aiNoticeTextWrap}>
            <Text style={styles.aiNoticeTitle}>AI-Generated Guidance — Verify with Supervisor</Text>
            <Text style={styles.aiNoticeSub}>
              Physical safety protocols must be confirmed with your plant area supervisor before taking high-risk action.
            </Text>
          </View>
        </View>

        {/* Human Review Inspection Flag */}
        {(ticket.flagged_for_human_review || visualAnalysis?.flagged_for_human_review) && (
          <View style={styles.humanReviewBanner}>
            <Text style={styles.humanReviewIcon}>🔍</Text>
            <View style={styles.humanReviewTextWrap}>
              <Text style={styles.humanReviewTitle}>Flagged for Physical Inspection</Text>
              <Text style={styles.humanReviewSub}>
                {ticket.review_reason || visualAnalysis?.human_review_reason || 'Visual evidence uncorroborated. Incident remains active for supervisor on-site review.'}
              </Text>
            </View>
          </View>
        )}

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
            <Text style={[
              styles.factValue,
              visualAnalysis ? { color: visualAnalysis.is_valid_evidence ? '#34d399' : '#f59e0b' } : undefined
            ]}>
              {visualAnalysis
                ? (visualAnalysis.is_valid_evidence
                    ? `Confirmed (${visualAnalysis.detected_event?.replace(/_/g, ' ')})`
                    : `Inconclusive (${visualAnalysis.detected_event?.replace(/_/g, ' ')} - Score Held Neutral)`)
                : (verifiedSummary?.observation_mode || 'Direct Observation')}
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

        {/* Rule-Based Severity Matrix Breakdown */}
        {ticket.severity_factors && (
          <View style={styles.card}>
            <View style={styles.matrixHeaderRow}>
              <Text style={styles.cardHeader}>Statutory Severity Matrix</Text>
              <View style={styles.advisoryBadge}>
                <Text style={styles.advisoryBadgeText}>ADVISORY ONLY</Text>
              </View>
            </View>
            <Text style={styles.matrixSub}>
              Formula: min(1.0, max(Base, Base × Likelihood × Consequence × Proximity))
            </Text>

            <View style={styles.matrixGrid}>
              <View style={styles.matrixCol}>
                <Text style={styles.matrixLabel}>Hazard Base</Text>
                <Text style={styles.matrixVal}>{ticket.severity_factors.hazard_base_severity || 0.70}</Text>
              </View>
              <View style={styles.matrixCol}>
                <Text style={styles.matrixLabel}>Likelihood</Text>
                <Text style={styles.matrixVal}>
                  {ticket.severity_factors.likelihood?.multiplier ? `×${ticket.severity_factors.likelihood.multiplier}` : '×1.0'}
                </Text>
              </View>
              <View style={styles.matrixCol}>
                <Text style={styles.matrixLabel}>Consequence</Text>
                <Text style={styles.matrixVal}>
                  {ticket.severity_factors.consequence?.multiplier ? `×${ticket.severity_factors.consequence.multiplier}` : '×1.0'}
                </Text>
              </View>
              <View style={styles.matrixCol}>
                <Text style={styles.matrixLabel}>Proximity</Text>
                <Text style={styles.matrixVal}>
                  {ticket.severity_factors.asset_proximity?.multiplier ? `×${ticket.severity_factors.asset_proximity.multiplier}` : '×1.0'}
                </Text>
              </View>
            </View>

            <View style={styles.finalScoreRow}>
              <Text style={styles.finalScoreLabel}>Final Auditable Severity Score:</Text>
              <Text style={styles.finalScoreVal}>{ticket.risk_score || ticket.severity_factors.calculated_risk_score || '0.75'}</Text>
            </View>
          </View>
        )}

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

        {/* AI Visual Verification Card */}
        {visualAnalysis && (
          <View style={[
            styles.card,
            visualAnalysis.is_valid_evidence ? styles.aiCardConfirmed : styles.aiCardInconclusive
          ]}>
            <View style={styles.aiHeaderRow}>
              <Text style={styles.aiHeaderTitle}>🤖 AI Visual Analysis</Text>
              <View style={[
                styles.aiStatusBadge,
                visualAnalysis.is_valid_evidence ? styles.aiBadgeConfirmed : styles.aiBadgeInconclusive
              ]}>
                <Text style={[
                  styles.aiStatusBadgeText,
                  visualAnalysis.is_valid_evidence ? styles.aiBadgeTextConfirmed : styles.aiBadgeTextInconclusive
                ]}>
                  {visualAnalysis.is_valid_evidence ? '✓ CONFIRMED' : '⚠️ INCONCLUSIVE'}
                </Text>
              </View>
            </View>

            <View style={styles.factRow}>
              <Text style={styles.factLabel}>Detected Event:</Text>
              <Text style={styles.factValue}>
                {visualAnalysis.detected_event?.replace(/_/g, ' ').toUpperCase()}
              </Text>
            </View>
            <View style={styles.factRow}>
              <Text style={styles.factLabel}>Model & License:</Text>
              <Text style={[styles.factValue, { color: '#38bdf8' }]}>
                {visualAnalysis.model_version || 'BSL-Vision-v2.5'} ({visualAnalysis.detector_license || 'Apache-2.0'})
              </Text>
            </View>
            <View style={styles.factRow}>
              <Text style={styles.factLabel}>Model Confidence:</Text>
              <Text style={styles.factValue}>
                {Math.round((visualAnalysis.confidence || 0) * 100)}%
              </Text>
            </View>
            {visualAnalysis.image_sha256 && (
              <View style={styles.factRow}>
                <Text style={styles.factLabel}>SHA-256 Hash:</Text>
                <Text style={[styles.factValue, { fontSize: 10, fontFamily: 'monospace' }]}>
                  {visualAnalysis.image_sha256.substring(0, 16)}...
                </Text>
              </View>
            )}
            <View style={styles.factRow}>
              <Text style={styles.factLabel}>Risk Score Impact:</Text>
              <Text style={[
                styles.factValue,
                { color: visualAnalysis.is_valid_evidence ? '#34d399' : '#f59e0b' }
              ]}>
                {visualAnalysis.is_valid_evidence ? 'Elevated via visual proof' : 'Held neutral (NOT inflated)'}
              </Text>
            </View>

            {/* Localized Object Bounding Boxes */}
            {visualAnalysis.evidence_boxes && visualAnalysis.evidence_boxes.length > 0 && (
              <View style={styles.boxChipsContainer}>
                <Text style={styles.boxChipsHeader}>Detected Objects & Localization:</Text>
                <View style={styles.boxChipsRow}>
                  {visualAnalysis.evidence_boxes.map((box: any, bIdx: number) => (
                    <View key={bIdx} style={[styles.boxChip, { borderColor: box.color || '#3b82f6' }]}>
                      <View style={[styles.boxChipDot, { backgroundColor: box.color || '#3b82f6' }]} />
                      <Text style={styles.boxChipText}>
                        {box.label} ({Math.round((box.confidence || 0) * 100)}%)
                      </Text>
                    </View>
                  ))}
                </View>
              </View>
            )}

            {/* Experimental Class Warning Banner */}
            {visualAnalysis.is_experimental && (
              <View style={styles.experimentalBanner}>
                <Text style={styles.experimentalBannerText}>
                  ⚠️ EXPERIMENTAL / NO VERIFIED PLANT DATA: Model prediction for '{visualAnalysis.detected_event}' is unvalidated. Do not rely on AI for this hazard class.
                </Text>
              </View>
            )}

            <Text style={styles.aiSummaryText}>
              {visualAnalysis.visual_summary}
            </Text>
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
  aiCardConfirmed: {
    borderColor: '#059669',
    backgroundColor: 'rgba(6, 78, 59, 0.25)',
  },
  aiCardInconclusive: {
    borderColor: '#d97706',
    backgroundColor: 'rgba(120, 53, 15, 0.25)',
  },
  aiHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  aiHeaderTitle: {
    color: '#38bdf8',
    fontSize: 13,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  aiStatusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    borderWidth: 1,
  },
  aiBadgeConfirmed: {
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
    borderColor: '#10b981',
  },
  aiBadgeInconclusive: {
    backgroundColor: 'rgba(245, 158, 11, 0.15)',
    borderColor: '#f59e0b',
  },
  aiStatusBadgeText: {
    fontSize: 10,
    fontWeight: '800',
  },
  aiBadgeTextConfirmed: {
    color: '#34d399',
  },
  aiBadgeTextInconclusive: {
    color: '#fbbf24',
  },
  aiSummaryText: {
    color: '#94a3b8',
    fontSize: 12,
    lineHeight: 18,
    fontStyle: 'italic',
    marginTop: 10,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.08)',
  },
  aiNoticeBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#451a03',
    borderWidth: 1.5,
    borderColor: '#f59e0b',
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
  },
  aiNoticeIcon: {
    fontSize: 22,
    marginRight: 10,
  },
  aiNoticeTextWrap: {
    flex: 1,
  },
  aiNoticeTitle: {
    color: '#fef3c7',
    fontSize: 13,
    fontWeight: '800',
    marginBottom: 2,
  },
  aiNoticeSub: {
    color: '#fde68a',
    fontSize: 11,
    lineHeight: 15,
  },
  humanReviewBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1e1b4b',
    borderWidth: 1.5,
    borderColor: '#818cf8',
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
  },
  humanReviewIcon: {
    fontSize: 22,
    marginRight: 10,
  },
  humanReviewTextWrap: {
    flex: 1,
  },
  humanReviewTitle: {
    color: '#e0e7ff',
    fontSize: 13,
    fontWeight: '800',
    marginBottom: 2,
  },
  humanReviewSub: {
    color: '#c7d2fe',
    fontSize: 11,
    lineHeight: 15,
  },
  matrixHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  advisoryBadge: {
    backgroundColor: '#3b0764',
    borderWidth: 1,
    borderColor: '#c084fc',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  advisoryBadgeText: {
    color: '#e9d5ff',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  matrixSub: {
    color: '#94a3b8',
    fontSize: 11,
    fontStyle: 'italic',
    marginBottom: 12,
  },
  matrixGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    backgroundColor: '#0f172a',
    padding: 10,
    borderRadius: 8,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#334155',
  },
  matrixCol: {
    alignItems: 'center',
  },
  matrixLabel: {
    color: '#64748b',
    fontSize: 10,
    fontWeight: '700',
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  matrixVal: {
    color: '#38bdf8',
    fontSize: 13,
    fontWeight: '800',
  },
  finalScoreRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#334155',
  },
  finalScoreLabel: {
    color: '#cbd5e1',
    fontSize: 12,
    fontWeight: '700',
  },
  finalScoreVal: {
    color: '#f43f5e',
    fontSize: 16,
    fontWeight: '900',
  },
  boxChipsContainer: {
    marginTop: 10,
    marginBottom: 8,
    backgroundColor: '#0f172a',
    padding: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#334155',
  },
  boxChipsHeader: {
    color: '#94a3b8',
    fontSize: 11,
    fontWeight: '700',
    marginBottom: 6,
    textTransform: 'uppercase',
  },
  boxChipsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  boxChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1e293b',
    borderWidth: 1,
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  boxChipDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  boxChipText: {
    color: '#f1f5f9',
    fontSize: 11,
    fontWeight: '600',
  },
  experimentalBanner: {
    backgroundColor: 'rgba(239, 68, 68, 0.15)',
    borderWidth: 1,
    borderColor: '#ef4444',
    borderRadius: 8,
    padding: 8,
    marginTop: 8,
    marginBottom: 6,
  },
  experimentalBannerText: {
    color: '#fca5a5',
    fontSize: 11,
    fontWeight: '700',
    lineHeight: 15,
  },
});
