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
          <Text style={styles.successTitle}>Incident Logged & Dispatched</Text>
          <Text style={styles.ticketIdText}>Ticket ID: {ticket.id}</Text>
        </View>

        {/* Safety-Critical AI Advisory Notice */}
        <View style={styles.aiNoticeBanner}>
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
              visualAnalysis ? { color: visualAnalysis.is_valid_evidence ? '#ffffff' : 'rgba(235, 235, 245, 0.7)' } : undefined
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
              <Text style={styles.aiHeaderTitle}>AI Visual Analysis</Text>
              <View style={[
                styles.aiStatusBadge,
                visualAnalysis.is_valid_evidence ? styles.aiBadgeConfirmed : styles.aiBadgeInconclusive
              ]}>
                <Text style={[
                  styles.aiStatusBadgeText,
                  visualAnalysis.is_valid_evidence ? styles.aiBadgeTextConfirmed : styles.aiBadgeTextInconclusive
                ]}>
                  {visualAnalysis.is_valid_evidence ? 'CONFIRMED' : 'INCONCLUSIVE'}
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
              <Text style={[styles.factValue, { color: '#ffffff' }]}>
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
                { color: visualAnalysis.is_valid_evidence ? '#ffffff' : 'rgba(235, 235, 245, 0.7)' }
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
                  EXPERIMENTAL / NO VERIFIED PLANT DATA: Model prediction for '{visualAnalysis.detected_event}' is unvalidated. Do not rely on AI for this hazard class.
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
    backgroundColor: '#000000',
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
    fontSize: 22,
    fontWeight: '700',
    marginBottom: 4,
    letterSpacing: -0.4,
  },
  ticketIdText: {
    color: 'rgba(235, 235, 245, 0.7)',
    fontSize: 13,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  badgeContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 8,
    marginBottom: 20,
  },
  threatBadge: {
    backgroundColor: '#2c2c2e',
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 9999,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  threatBadgeText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '700',
  },
  categoryBadge: {
    backgroundColor: '#1c1c1e',
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 9999,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.15)',
  },
  categoryBadgeText: {
    color: 'rgba(235, 235, 245, 0.85)',
    fontSize: 12,
    fontWeight: '700',
  },
  card: {
    backgroundColor: '#1c1c1e',
    borderRadius: 20,
    padding: 18,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
    marginBottom: 16,
  },
  cardHeader: {
    color: 'rgba(235, 235, 245, 0.65)',
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.2,
    marginBottom: 12,
  },
  narrativeText: {
    color: 'rgba(235, 235, 245, 0.85)',
    fontSize: 14,
    lineHeight: 21,
  },
  factRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 0.5,
    borderBottomColor: 'rgba(255, 255, 255, 0.08)',
  },
  factLabel: {
    color: 'rgba(235, 235, 245, 0.55)',
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
    borderRadius: 16,
  },
  recipientRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
  },
  recipientDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#ffffff',
    marginRight: 10,
  },
  recipientInfo: {
    flex: 1,
  },
  recipientDept: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
  recipientSub: {
    color: 'rgba(235, 235, 245, 0.45)',
    fontSize: 11,
    marginTop: 1,
  },
  newReportButton: {
    backgroundColor: '#ffffff',
    minHeight: 52,
    borderRadius: 9999,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 14,
  },
  newReportButtonText: {
    color: '#000000',
    fontSize: 16,
    fontWeight: '600',
    letterSpacing: -0.2,
  },
  aiCardConfirmed: {
    borderColor: 'rgba(255, 255, 255, 0.2)',
    backgroundColor: '#1c1c1e',
  },
  aiCardInconclusive: {
    borderColor: 'rgba(255, 255, 255, 0.15)',
    backgroundColor: '#1c1c1e',
  },
  aiHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  aiHeaderTitle: {
    color: 'rgba(235, 235, 245, 0.65)',
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.2,
  },
  aiStatusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 9999,
    borderWidth: 1,
  },
  aiBadgeConfirmed: {
    backgroundColor: '#2c2c2e',
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  aiBadgeInconclusive: {
    backgroundColor: '#1c1c1e',
    borderColor: 'rgba(255, 255, 255, 0.15)',
  },
  aiStatusBadgeText: {
    fontSize: 11,
    fontWeight: '600',
  },
  aiBadgeTextConfirmed: {
    color: '#ffffff',
  },
  aiBadgeTextInconclusive: {
    color: 'rgba(235, 235, 245, 0.7)',
  },
  aiSummaryText: {
    color: 'rgba(235, 235, 245, 0.65)',
    fontSize: 13,
    lineHeight: 18,
    fontStyle: 'italic',
    marginTop: 10,
    paddingTop: 8,
    borderTopWidth: 0.5,
    borderTopColor: 'rgba(255, 255, 255, 0.08)',
  },
  aiNoticeBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1c1c1e',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.15)',
    borderRadius: 18,
    padding: 14,
    marginBottom: 14,
  },
  aiNoticeIcon: {
    fontSize: 22,
    marginRight: 10,
  },
  aiNoticeTextWrap: {
    flex: 1,
  },
  aiNoticeTitle: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '700',
    marginBottom: 2,
  },
  aiNoticeSub: {
    color: 'rgba(235, 235, 245, 0.7)',
    fontSize: 12,
    lineHeight: 16,
  },
  humanReviewBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1c1c1e',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.15)',
    borderRadius: 18,
    padding: 14,
    marginBottom: 14,
  },
  humanReviewIcon: {
    fontSize: 22,
    marginRight: 10,
  },
  humanReviewTextWrap: {
    flex: 1,
  },
  humanReviewTitle: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '700',
    marginBottom: 2,
  },
  humanReviewSub: {
    color: 'rgba(235, 235, 245, 0.7)',
    fontSize: 12,
    lineHeight: 16,
  },
  matrixHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  advisoryBadge: {
    backgroundColor: '#2c2c2e',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 9999,
  },
  advisoryBadgeText: {
    color: '#ffffff',
    fontSize: 11,
    fontWeight: '600',
  },
  matrixSub: {
    color: 'rgba(235, 235, 245, 0.45)',
    fontSize: 12,
    marginBottom: 14,
  },
  matrixGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    backgroundColor: 'rgba(255, 255, 255, 0.04)',
    padding: 12,
    borderRadius: 14,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
  },
  matrixCol: {
    alignItems: 'center',
  },
  matrixLabel: {
    color: 'rgba(235, 235, 245, 0.45)',
    fontSize: 10,
    fontWeight: '600',
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  matrixVal: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '700',
  },
  finalScoreRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 10,
    borderTopWidth: 0.5,
    borderTopColor: 'rgba(255, 255, 255, 0.08)',
  },
  finalScoreLabel: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '600',
  },
  finalScoreVal: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
  },
  boxChipsContainer: {
    marginTop: 10,
    marginBottom: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.04)',
    padding: 12,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
  },
  boxChipsHeader: {
    color: 'rgba(235, 235, 245, 0.55)',
    fontSize: 11,
    fontWeight: '600',
    marginBottom: 8,
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
    backgroundColor: '#2c2c2e',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 9999,
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  boxChipDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  boxChipText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '500',
  },
  experimentalBanner: {
    backgroundColor: 'rgba(255, 69, 58, 0.12)',
    borderWidth: 1,
    borderColor: 'rgba(255, 69, 58, 0.3)',
    borderRadius: 14,
    padding: 10,
    marginTop: 8,
    marginBottom: 6,
  },
  experimentalBannerText: {
    color: '#FF453A',
    fontSize: 11,
    fontWeight: '600',
    lineHeight: 15,
  },
});
