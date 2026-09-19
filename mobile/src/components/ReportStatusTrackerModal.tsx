import React, { useState } from 'react';
import {
  Modal,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { getIncidentTracker, IncidentTrackerData } from '../services/api';
import { i18n } from '../services/i18n';

interface Props {
  visible: boolean;
  onClose: () => void;
  initialCode?: string;
}

const STAGES = [
  { key: 'received', labelEn: 'Received', labelHi: 'प्राप्त हुआ', icon: '📥' },
  { key: 'under_review', labelEn: 'Under Review', labelHi: 'समीक्षाधीन', icon: '🔍' },
  { key: 'action_assigned', labelEn: 'Action Assigned', labelHi: 'कार्रवाई सौंपी गई', icon: '🛠️' },
  { key: 'action_taken', labelEn: 'Action Taken', labelHi: 'कार्रवाई की गई', icon: '🚧' },
  { key: 'resolved', labelEn: 'Hazard Resolved', labelHi: 'जोखिम का समाधान', icon: '✅' },
];

export const ReportStatusTrackerModal: React.FC<Props> = ({ visible, onClose, initialCode }) => {
  const [code, setCode] = useState(initialCode || '');
  const [loading, setLoading] = useState(false);
  const [trackerData, setTrackerData] = useState<IncidentTrackerData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleTrack = async () => {
    if (!code.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getIncidentTracker(code.trim());
      setTrackerData(data);
    } catch (err: any) {
      setError(err.message || 'Report not found. Please check your tracking code.');
      setTrackerData(null);
    } finally {
      setLoading(false);
    }
  };

  const getStageIndex = (stage: string) => {
    const idx = STAGES.findIndex((s) => s.key === stage);
    return idx >= 0 ? idx : 0;
  };

  const currentStageIndex = trackerData ? getStageIndex(trackerData.lifecycle_stage) : 0;

  return (
    <Modal visible={visible} animationType="slide" transparent>
      <View style={styles.overlay}>
        <View style={styles.container}>
          <View style={styles.header}>
            <View>
              <Text style={styles.title}>📍 Near-Miss Status Tracker</Text>
              <Text style={styles.subtitle}>रिपोर्ट की स्थिति जानें (Never lost in a black hole)</Text>
            </View>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Text style={styles.closeText}>✕</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.searchRow}>
            <TextInput
              style={styles.input}
              placeholder="Enter Tracking Code (e.g. NM-A1B2C3) or Ticket ID"
              placeholderTextColor="#64748b"
              value={code}
              onChangeText={setCode}
              autoCapitalize="characters"
            />
            <TouchableOpacity style={styles.trackButton} onPress={handleTrack} disabled={loading}>
              {loading ? (
                <ActivityIndicator color="#ffffff" size="small" />
              ) : (
                <Text style={styles.trackButtonText}>Track</Text>
              )}
            </TouchableOpacity>
          </View>

          {error && (
            <View style={styles.errorBox}>
              <Text style={styles.errorText}>⚠️ {error}</Text>
            </View>
          )}

          <ScrollView style={styles.contentScroll}>
            {trackerData ? (
              <View style={styles.resultCard}>
                <View style={styles.resultHeader}>
                  <View>
                    <Text style={styles.resultId}>
                      {trackerData.is_anonymous ? '🔒 Anonymous Report' : `Ticket #${trackerData.ticket_id.slice(0, 8)}`}
                    </Text>
                    {trackerData.anonymous_tracking_code && (
                      <Text style={styles.trackingCodePill}>
                        Code: {trackerData.anonymous_tracking_code}
                      </Text>
                    )}
                  </View>
                  <View
                    style={[
                      styles.statusPill,
                      trackerData.status === 'resolved' ? styles.statusPillResolved : styles.statusPillOpen,
                    ]}
                  >
                    <Text style={styles.statusPillText}>{trackerData.status.toUpperCase()}</Text>
                  </View>
                </View>

                {trackerData.is_anonymous && (
                  <View style={styles.anonymousNotice}>
                    <Text style={styles.anonymousNoticeText}>
                      🛡️ Protected No-Blame Report: Attributed to Shift {trackerData.shift || 'General'} & Zone {trackerData.zone_id || 'General'}. Identity strictly unrecorded.
                    </Text>
                  </View>
                )}

                <Text style={styles.descriptionLabel}>Reported Hazard:</Text>
                <Text style={styles.descriptionText}>{trackerData.description}</Text>

                {/* Milestone Progression Timeline */}
                <Text style={styles.timelineTitle}>Resolution Milestones / समाधान चरण:</Text>
                <View style={styles.timelineContainer}>
                  {STAGES.map((s, idx) => {
                    const isPassed = idx <= currentStageIndex;
                    const isCurrent = idx === currentStageIndex;
                    return (
                      <View key={s.key} style={styles.timelineStep}>
                        <View
                          style={[
                            styles.circle,
                            isPassed ? styles.circlePassed : styles.circlePending,
                            isCurrent && styles.circleCurrent,
                          ]}
                        >
                          <Text style={styles.circleIcon}>{isPassed ? s.icon : '○'}</Text>
                        </View>
                        <View style={styles.stepInfo}>
                          <Text style={[styles.stepLabelEn, isPassed && styles.stepLabelPassed]}>
                            {s.labelEn}
                          </Text>
                          <Text style={styles.stepLabelHi}>{s.labelHi}</Text>
                        </View>
                      </View>
                    );
                  })}
                </View>

                {/* Corrective Action Section */}
                <View style={styles.actionSection}>
                  <Text style={styles.actionHeader}>🛠️ Corrective Action & Closure Status</Text>
                  {trackerData.corrective_action ? (
                    <View style={styles.actionDetails}>
                      <Text style={styles.actionTitle}>Assigned Fix:</Text>
                      <Text style={styles.actionValue}>{trackerData.corrective_action}</Text>
                      <View style={styles.actionRow}>
                        <Text style={styles.actionMeta}>
                          👤 Assigned To: <Text style={styles.actionHighlight}>{trackerData.assigned_to || 'Maintenance Team'}</Text>
                        </Text>
                        {trackerData.due_date && (
                          <Text style={styles.actionMeta}>
                            📅 Target: <Text style={styles.actionHighlight}>{new Date(trackerData.due_date).toLocaleDateString()}</Text>
                          </Text>
                        )}
                      </View>
                    </View>
                  ) : (
                    <Text style={styles.pendingActionText}>
                      Safety officer triage in progress. Corrective task will be assigned shortly.
                    </Text>
                  )}

                  {trackerData.closure_notes && (
                    <View style={styles.closureBox}>
                      <Text style={styles.closureTitle}>✅ Verification & Resolution Evidence:</Text>
                      <Text style={styles.closureNotes}>{trackerData.closure_notes}</Text>
                      {trackerData.closure_time_hours != null && (
                        <Text style={styles.turnaroundPill}>
                          ⚡ Hazard permanently fixed in {trackerData.closure_time_hours} hours from reporting
                        </Text>
                      )}
                    </View>
                  )}
                </View>

                {/* Audit Event Trail */}
                {trackerData.history_events.length > 0 && (
                  <View style={styles.auditSection}>
                    <Text style={styles.auditTitle}>📜 Activity Log</Text>
                    {trackerData.history_events.map((evt) => (
                      <View key={evt.id} style={styles.auditRow}>
                        <Text style={styles.auditAction}>• {evt.action.replace(/_/g, ' ')}</Text>
                        <Text style={styles.auditRole}>({evt.actor_role})</Text>
                        <Text style={styles.auditTime}>
                          {new Date(evt.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </Text>
                      </View>
                    ))}
                  </View>
                )}
              </View>
            ) : (
              <View style={styles.emptyState}>
                <Text style={styles.emptyIcon}>🔍</Text>
                <Text style={styles.emptyTitle}>Track Any Safety Report</Text>
                <Text style={styles.emptySubtitle}>
                  Every report filed gets a tracking code. Use it here to see what action maintenance and safety teams took to protect your workplace.
                </Text>
              </View>
            )}
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.85)',
    justifyContent: 'flex-end',
  },
  container: {
    backgroundColor: '#0c1524',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    maxHeight: '92%',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: '800',
    color: '#ffffff',
  },
  subtitle: {
    fontSize: 12,
    color: '#94a3b8',
    marginTop: 2,
  },
  closeButton: {
    padding: 8,
    backgroundColor: '#1e293b',
    borderRadius: 16,
  },
  closeText: {
    color: '#ffffff',
    fontWeight: 'bold',
    fontSize: 14,
  },
  searchRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 14,
  },
  input: {
    flex: 1,
    backgroundColor: '#070d18',
    borderWidth: 1,
    borderColor: '#334155',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: '#ffffff',
    fontSize: 13,
  },
  trackButton: {
    backgroundColor: '#38bdf8',
    paddingHorizontal: 18,
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 8,
  },
  trackButtonText: {
    color: '#070d18',
    fontWeight: '800',
    fontSize: 14,
  },
  errorBox: {
    backgroundColor: 'rgba(239, 68, 68, 0.15)',
    borderWidth: 1,
    borderColor: '#ef4444',
    padding: 10,
    borderRadius: 8,
    marginBottom: 12,
  },
  errorText: {
    color: '#ef4444',
    fontSize: 12,
  },
  contentScroll: {
    maxHeight: 520,
  },
  resultCard: {
    backgroundColor: '#0f1d32',
    borderWidth: 1,
    borderColor: '#1e293b',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 10,
  },
  resultId: {
    color: '#ffffff',
    fontWeight: '800',
    fontSize: 15,
  },
  trackingCodePill: {
    color: '#38bdf8',
    fontSize: 12,
    fontWeight: '700',
    marginTop: 2,
  },
  statusPill: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusPillOpen: {
    backgroundColor: 'rgba(245, 158, 11, 0.2)',
    borderColor: '#f59e0b',
    borderWidth: 1,
  },
  statusPillResolved: {
    backgroundColor: 'rgba(16, 185, 129, 0.2)',
    borderColor: '#10b981',
    borderWidth: 1,
  },
  statusPillText: {
    color: '#ffffff',
    fontSize: 11,
    fontWeight: '800',
  },
  anonymousNotice: {
    backgroundColor: 'rgba(99, 102, 241, 0.12)',
    borderWidth: 1,
    borderColor: '#6366f1',
    borderRadius: 8,
    padding: 8,
    marginBottom: 12,
  },
  anonymousNoticeText: {
    color: '#c7d2fe',
    fontSize: 11,
    lineHeight: 16,
  },
  descriptionLabel: {
    color: '#64748b',
    fontSize: 11,
    fontWeight: '700',
    marginBottom: 2,
  },
  descriptionText: {
    color: '#e2e8f0',
    fontSize: 13,
    marginBottom: 16,
  },
  timelineTitle: {
    color: '#94a3b8',
    fontSize: 12,
    fontWeight: '800',
    marginBottom: 10,
    textTransform: 'uppercase',
  },
  timelineContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    backgroundColor: '#070d18',
    borderRadius: 10,
    padding: 12,
    marginBottom: 16,
  },
  timelineStep: {
    alignItems: 'center',
    flex: 1,
  },
  circle: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 6,
  },
  circlePassed: {
    backgroundColor: 'rgba(16, 185, 129, 0.25)',
    borderWidth: 1.5,
    borderColor: '#10b981',
  },
  circlePending: {
    backgroundColor: '#1e293b',
    borderWidth: 1,
    borderColor: '#334155',
  },
  circleCurrent: {
    borderColor: '#38bdf8',
    borderWidth: 2,
    backgroundColor: 'rgba(56, 189, 248, 0.25)',
  },
  circleIcon: {
    fontSize: 13,
    color: '#ffffff',
  },
  stepInfo: {
    alignItems: 'center',
  },
  stepLabelEn: {
    fontSize: 9,
    color: '#64748b',
    fontWeight: '700',
    textAlign: 'center',
  },
  stepLabelPassed: {
    color: '#ffffff',
  },
  stepLabelHi: {
    fontSize: 8,
    color: '#475569',
    textAlign: 'center',
  },
  actionSection: {
    backgroundColor: '#070d18',
    borderRadius: 10,
    padding: 12,
    marginBottom: 14,
  },
  actionHeader: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '800',
    marginBottom: 8,
  },
  actionDetails: {
    backgroundColor: '#0c1524',
    borderRadius: 8,
    padding: 10,
    marginBottom: 6,
  },
  actionTitle: {
    color: '#94a3b8',
    fontSize: 11,
    fontWeight: '700',
  },
  actionValue: {
    color: '#38bdf8',
    fontSize: 13,
    fontWeight: '800',
    marginTop: 2,
    marginBottom: 6,
  },
  actionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 4,
  },
  actionMeta: {
    color: '#64748b',
    fontSize: 11,
  },
  actionHighlight: {
    color: '#e2e8f0',
    fontWeight: '700',
  },
  pendingActionText: {
    color: '#94a3b8',
    fontSize: 12,
    fontStyle: 'italic',
  },
  closureBox: {
    marginTop: 10,
    backgroundColor: 'rgba(16, 185, 129, 0.1)',
    borderWidth: 1,
    borderColor: '#10b981',
    borderRadius: 8,
    padding: 10,
  },
  closureTitle: {
    color: '#10b981',
    fontSize: 11,
    fontWeight: '800',
    marginBottom: 4,
  },
  closureNotes: {
    color: '#ffffff',
    fontSize: 12,
    lineHeight: 16,
  },
  turnaroundPill: {
    marginTop: 8,
    color: '#34d399',
    fontSize: 11,
    fontWeight: '800',
  },
  auditSection: {
    marginTop: 8,
  },
  auditTitle: {
    color: '#64748b',
    fontSize: 11,
    fontWeight: '700',
    marginBottom: 6,
    textTransform: 'uppercase',
  },
  auditRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 4,
  },
  auditAction: {
    color: '#94a3b8',
    fontSize: 11,
    fontWeight: '600',
  },
  auditRole: {
    color: '#475569',
    fontSize: 10,
  },
  auditTime: {
    color: '#475569',
    fontSize: 10,
    marginLeft: 'auto',
  },
  emptyState: {
    alignItems: 'center',
    padding: 30,
  },
  emptyIcon: {
    fontSize: 36,
    marginBottom: 10,
  },
  emptyTitle: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '800',
    marginBottom: 6,
  },
  emptySubtitle: {
    color: '#94a3b8',
    fontSize: 12,
    textAlign: 'center',
    lineHeight: 18,
  },
});
