import React, { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import {
  useAudioRecorder,
  RecordingPresets,
  setAudioModeAsync,
  requestRecordingPermissionsAsync,
} from 'expo-audio';
import { INTAKE_LANGUAGES } from '../services/config';
import { createIncidentFromAudio, createIncidentFromText, Ticket } from '../services/api';
import { StepIndicator } from '../components/StepIndicator';
import { ZoneRestrictionBanner, RESTRICTED_ZONES_MAP } from '../components/ZoneRestrictionBanner';
import { KioskSession } from './KioskLoginScreen';
import { i18n } from '../services/i18n';
import { outbox } from '../services/outbox';

interface IncidentRecorderScreenProps {
  reportType: 'emergency' | 'suspected';
  onIncidentCreated: (ticket: Ticket) => void;
  onBack: () => void;
  kioskSession?: KioskSession | null;
  onSwitchToKiosk?: () => void;
}

const COMMON_ZONES = [
  { id: 'BF1', name: 'Blast Furnace 1' },
  { id: 'BF2', name: 'Blast Furnace 2' },
  { id: 'COB', name: 'Coke Oven Battery' },
  { id: 'GHS', name: 'Gas Holder Station' },
  { id: 'SMS', name: 'Steel Melting Shop' },
  { id: 'CC', name: 'Continuous Casting' },
  { id: 'RMY', name: 'Raw Material Yard' },
  { id: 'HSM', name: 'Hot Strip Mill' },
];

export const IncidentRecorderScreen: React.FC<IncidentRecorderScreenProps> = ({
  reportType,
  onIncidentCreated,
  onBack,
  kioskSession,
  onSwitchToKiosk,
}) => {
  const [mode, setMode] = useState<'voice' | 'text'>('voice');
  const [selectedLanguage, setSelectedLanguage] = useState<string>(i18n.getLanguage());
  const [selectedZone, setSelectedZone] = useState<string>('BF1');
  const [textInput, setTextInput] = useState<string>('');
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [transcribedTicket, setTranscribedTicket] = useState<Ticket | null>(null);

  const audioRecorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);

  const startRecording = async () => {
    try {
      setStatusMessage('Requesting microphone permission...');
      const perm = await requestRecordingPermissionsAsync();
      if (!perm.granted) {
        Alert.alert(
          'Microphone Access Needed',
          'Please allow microphone access to record voice incident reports.'
        );
        return;
      }

      await setAudioModeAsync({
        allowsRecording: true,
        playsInSilentMode: true,
      });

      setStatusMessage('Recording speech... Tap button again when done.');
      await audioRecorder.prepareToRecordAsync();
      audioRecorder.record();
      setIsRecording(true);
    } catch (err: any) {
      Alert.alert('Recording Error', err.message || 'Could not start recording.');
      setIsRecording(false);
    }
  };

  const stopRecordingAndTranscribe = async () => {
    try {
      setIsRecording(false);
      setIsLoading(true);
      setStatusMessage('Transcribing speech with on-premise Whisper & plant domain vocabulary...');

      await audioRecorder.stop();
      const uri = audioRecorder.uri;

      if (!uri) {
        throw new Error('No recorded audio file found.');
      }

      try {
        const ticket = await createIncidentFromAudio(uri, reportType, selectedLanguage);
        setIsLoading(false);
        // Show transcript confirmation screen before proceeding
        setTranscribedTicket(ticket);
      } catch (uploadErr: any) {
        // Offline Outbox Fallback: Queue audio report locally
        console.log('[IncidentRecorder] Network upload failed, enqueuing audio to Outbox...');
        await outbox.enqueue('incident_audio', {
          audioUri: uri,
          reportType,
          language: selectedLanguage,
          zone_id: selectedZone,
          employee_id: kioskSession?.workerBadgeId,
        });
        setIsLoading(false);

        // Construct optimistic offline ticket
        const offlineTicket: Ticket = {
          id: `offline_${Date.now()}`,
          report_type: reportType,
          incident_description: '[OFFLINE AUDIO REPORT QUEUED IN OUTBOX]',
          predicted_category: reportType === 'emergency' ? 'fire' : 'mechanical_failure',
          risk_score: reportType === 'emergency' ? 0.85 : 0.60,
          routing_tier: reportType === 'emergency' ? 'emergency_authority' : 'log_only',
          verification_status: 'offline_queued',
          zone_id: selectedZone,
        };
        Alert.alert(
          'Report Stored in Outbox',
          'You are currently offline. Your audio note has been saved to your persistent outbox and will automatically sync when connectivity returns.'
        );
        onIncidentCreated(offlineTicket);
      }
    } catch (err: any) {
      setIsLoading(false);
      Alert.alert('Recording Error', err.message || 'Could not complete audio recording.');
    }
  };

  const submitText = async () => {
    if (!textInput.trim()) {
      Alert.alert('Required', 'Please type a description of the safety observation.');
      return;
    }
    try {
      setIsLoading(true);
      setStatusMessage('Submitting incident notice...');
      try {
        const ticket = await createIncidentFromText({
          report_type: reportType,
          incident_description: textInput.trim(),
          language: selectedLanguage,
          zone_id: selectedZone,
        });
        setIsLoading(false);
        onIncidentCreated(ticket);
      } catch (err: any) {
        // Offline Outbox Fallback
        console.log('[IncidentRecorder] Network failed, enqueuing text report to Outbox...');
        await outbox.enqueue('incident_report', {
          report_type: reportType,
          incident_description: textInput.trim(),
          language: selectedLanguage,
          zone_id: selectedZone,
          employee_id: kioskSession?.workerBadgeId,
        });
        setIsLoading(false);

        const offlineTicket: Ticket = {
          id: `offline_${Date.now()}`,
          report_type: reportType,
          incident_description: textInput.trim(),
          predicted_category: reportType === 'emergency' ? 'fire' : 'mechanical_failure',
          risk_score: reportType === 'emergency' ? 0.85 : 0.60,
          routing_tier: reportType === 'emergency' ? 'emergency_authority' : 'log_only',
          verification_status: 'offline_queued',
          zone_id: selectedZone,
        };
        Alert.alert(
          'Report Stored in Outbox',
          'You are currently offline. Your report has been saved to the outbox and will auto-sync when network returns.'
        );
        onIncidentCreated(offlineTicket);
      }
    } catch (err: any) {
      setIsLoading(false);
      Alert.alert('Submission Failed', err.message || 'Failed to submit report.');
    }
  };

  // If transcript is ready, render the Transcript Review & Confirmation Modal
  if (transcribedTicket) {
    return (
      <ScrollView contentContainerStyle={styles.container}>
        <View style={styles.reviewModalCard}>
          <View style={styles.reviewHeaderRow}>
            <Text style={styles.reviewTitle}>🎙️ Confirm Speech Transcript</Text>
            <View style={styles.confBadge}>
              <Text style={styles.confBadgeText}>
                Confidence: {Math.round((transcribedTicket.language_confidence || 0.9) * 100)}%
              </Text>
            </View>
          </View>

          <Text style={styles.reviewSub}>
            Please verify that your reported statement was captured accurately before response crews are alerted:
          </Text>

          {/* Original Transcribed Text */}
          <View style={styles.transcriptBox}>
            <Text style={styles.boxLabel}>RECORDED SPEECH TRANSCRIPT:</Text>
            <Text style={styles.transcriptText}>
              "{transcribedTicket.incident_description}"
            </Text>
          </View>

          {/* English Operational Translation */}
          {transcribedTicket.incident_description_en && (
            <View style={[styles.transcriptBox, { borderColor: '#38bdf8' }]}>
              <Text style={[styles.boxLabel, { color: '#38bdf8' }]}>ENGLISH OPERATIONAL TRANSLATION:</Text>
              <Text style={styles.transcriptTextEn}>
                "{transcribedTicket.incident_description_en}"
              </Text>
            </View>
          )}

          {/* Low Confidence Critical Word Clarification Prompt */}
          {transcribedTicket.clarification_prompt && (
            <View style={styles.clarificationBanner}>
              <Text style={styles.clarificationTitle}>⚠️ ASR CONFIRMATION REQUIRED:</Text>
              <Text style={styles.clarificationText}>
                {transcribedTicket.clarification_prompt}
              </Text>
            </View>
          )}

          {/* Action Buttons (PPE Glove Sized >= 64px) */}
          <TouchableOpacity
            style={styles.confirmButton}
            onPress={() => onIncidentCreated(transcribedTicket)}
          >
            <Text style={styles.confirmButtonText}>Confirm Transcript & Proceed ➔</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.rerecordButton}
            onPress={() => setTranscribedTicket(null)}
          >
            <Text style={styles.rerecordButtonText}>↺ Tap to Re-record Speech</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    );
  }

  return (
    <View style={styles.container}>
      <StepIndicator currentStep={1} />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Kiosk or Supervisor Proxy Mode Header */}
        {kioskSession && (
          <View style={styles.kioskHeaderRow}>
            <Text style={styles.kioskIcon}>🏢</Text>
            <View style={{ flex: 1 }}>
              <Text style={styles.kioskTitle}>
                {kioskSession.reportingMode === 'supervisor_proxy'
                  ? `SUPERVISOR PROXY (By ${kioskSession.supervisorId || 'Supervisor'})`
                  : 'SHARED KIOSK TERMINAL'}
              </Text>
              <Text style={styles.kioskSub}>
                Worker Badge: <Text style={{ color: '#38bdf8', fontWeight: '800' }}>{kioskSession.workerBadgeId}</Text> • Station: {kioskSession.kioskStationId}
              </Text>
            </View>
          </View>
        )}

        {/* Top bar */}
        <View style={styles.topBar}>
          <TouchableOpacity onPress={onBack} style={styles.backButton}>
            <Text style={styles.backButtonText}>‹ Back</Text>
          </TouchableOpacity>
          <View style={styles.typeBadge}>
            <Text style={styles.typeBadgeText}>
              {reportType === 'emergency' ? '🚨 CRITICAL EMERGENCY' : '⚠️ INCIDENT OBSERVATION'}
            </Text>
          </View>
        </View>

        <Text style={styles.screenTitle}>
          {reportType === 'emergency' ? 'Emergency Incident Notice' : 'Describe What Happened'}
        </Text>
        <Text style={styles.screenSubtitle}>
          Voice-first reporting with automated steel plant domain transcription and noise suppression.
        </Text>

        {/* Zone Restriction Banner */}
        <ZoneRestrictionBanner
          zoneId={selectedZone}
          onUseKiosk={onSwitchToKiosk}
        />

        {/* Zone Selection Chips */}
        <Text style={styles.sectionLabel}>OBSERVED PLANT ZONE:</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.zoneScroll}>
          {COMMON_ZONES.map((z) => {
            const isRestricted = z.id in RESTRICTED_ZONES_MAP;
            const isSelected = selectedZone === z.id;
            return (
              <TouchableOpacity
                key={z.id}
                style={[
                  styles.zoneChip,
                  isSelected && styles.zoneChipSelected,
                  isRestricted && styles.zoneChipRestricted,
                ]}
                onPress={() => setSelectedZone(z.id)}
              >
                <Text style={[styles.zoneText, isSelected && styles.zoneTextSelected]}>
                  {isRestricted ? '⛔ ' : '📍 '}
                  {z.name} ({z.id})
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>

        {/* Mode Switcher */}
        <View style={styles.tabContainer}>
          <TouchableOpacity
            style={[styles.tabButton, mode === 'voice' && styles.tabButtonActive]}
            onPress={() => setMode('voice')}
          >
            <Text style={[styles.tabText, mode === 'voice' && styles.tabTextActive]}>
              🎙️ Voice Report (Primary)
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tabButton, mode === 'text' && styles.tabButtonActive]}
            onPress={() => setMode('text')}
          >
            <Text style={[styles.tabText, mode === 'text' && styles.tabTextActive]}>
              ✍️ Type Text
            </Text>
          </TouchableOpacity>
        </View>

        {/* Language Selection Chips */}
        <Text style={styles.sectionLabel}>SPOKEN LANGUAGE PREFERENCE:</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.langScroll}>
          {INTAKE_LANGUAGES.map((l) => (
            <TouchableOpacity
              key={l.code}
              style={[styles.langChip, selectedLanguage === l.code && styles.langChipActive]}
              onPress={() => setSelectedLanguage(l.code)}
            >
              <Text style={[styles.langText, selectedLanguage === l.code && styles.langTextActive]}>
                {l.label}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* Regional Dialect Warning */}
        {(selectedLanguage === 'bn' || selectedLanguage === 'or') && (
          <View style={styles.dialectWarningBox}>
            <Text style={styles.dialectWarningText}>{i18n.t('dialectNotice')}</Text>
          </View>
        )}

        {/* Voice Mode (PPE / Glove Friendly Giant Trigger) */}
        {mode === 'voice' && (
          <View style={styles.voiceSection}>
            <TouchableOpacity
              style={[
                styles.micHeroButton,
                isRecording ? styles.micHeroRecording : styles.micHeroIdle,
              ]}
              onPress={isRecording ? stopRecordingAndTranscribe : startRecording}
              disabled={isLoading}
              activeOpacity={0.8}
            >
              <Text style={styles.micIcon}>{isRecording ? '⏹️' : '🎙️'}</Text>
              <Text style={styles.micActionText}>
                {isRecording ? 'Tap to Stop & Transcribe' : 'Tap Giant Mic to Speak'}
              </Text>
              <Text style={styles.micSubText}>
                {isRecording ? 'Acoustic noise filter active...' : 'One-handed, glove-friendly trigger'}
              </Text>
            </TouchableOpacity>

            {isRecording && (
              <View style={styles.recordingPulseBar}>
                <View style={styles.redDot} />
                <Text style={styles.recordingStatusText}>Recording in progress... Tap to finish</Text>
              </View>
            )}
          </View>
        )}

        {/* Text Mode */}
        {mode === 'text' && (
          <View style={styles.textSection}>
            <TextInput
              style={styles.textArea}
              placeholder="e.g. Molten slag overflow near casthouse tuyere, LOTO applied at breaker panel..."
              placeholderTextColor="#64748b"
              multiline
              numberOfLines={4}
              value={textInput}
              onChangeText={setTextInput}
              editable={!isLoading}
            />
            <TouchableOpacity
              style={styles.submitTextButton}
              onPress={submitText}
              disabled={isLoading}
            >
              <Text style={styles.submitTextButtonText}>Submit Incident Notice ➔</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Loading Spinner */}
        {isLoading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#38bdf8" />
            <Text style={styles.loadingText}>{statusMessage}</Text>
          </View>
        )}
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
  kioskHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0f172a',
    borderWidth: 1.5,
    borderColor: '#38bdf8',
    padding: 10,
    borderRadius: 8,
    marginBottom: 12,
    gap: 10,
  },
  kioskIcon: {
    fontSize: 22,
  },
  kioskTitle: {
    color: '#38bdf8',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  kioskSub: {
    color: '#e2e8f0',
    fontSize: 12,
  },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  backButton: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    backgroundColor: '#1e293b',
    borderRadius: 8,
  },
  backButtonText: {
    color: '#94a3b8',
    fontSize: 13,
    fontWeight: '700',
  },
  typeBadge: {
    backgroundColor: '#1e293b',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
  },
  typeBadgeText: {
    color: '#f8fafc',
    fontSize: 11,
    fontWeight: '800',
  },
  screenTitle: {
    fontSize: 22,
    fontWeight: '900',
    color: '#ffffff',
    marginBottom: 4,
  },
  screenSubtitle: {
    fontSize: 13,
    color: '#94a3b8',
    marginBottom: 14,
  },
  sectionLabel: {
    color: '#64748b',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.5,
    marginBottom: 8,
    textTransform: 'uppercase',
  },
  zoneScroll: {
    marginBottom: 14,
  },
  zoneChip: {
    backgroundColor: '#0f172a',
    borderWidth: 1.5,
    borderColor: '#334155',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    marginRight: 8,
  },
  zoneChipSelected: {
    borderColor: '#38bdf8',
    backgroundColor: 'rgba(56, 189, 248, 0.15)',
  },
  zoneChipRestricted: {
    borderColor: '#ef4444',
  },
  zoneText: {
    color: '#94a3b8',
    fontSize: 12,
    fontWeight: '700',
  },
  zoneTextSelected: {
    color: '#ffffff',
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#0f172a',
    borderRadius: 12,
    padding: 4,
    marginBottom: 16,
  },
  tabButton: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    borderRadius: 8,
  },
  tabButtonActive: {
    backgroundColor: '#1e293b',
  },
  tabText: {
    color: '#64748b',
    fontSize: 13,
    fontWeight: '700',
  },
  tabTextActive: {
    color: '#ffffff',
  },
  langScroll: {
    marginBottom: 16,
  },
  langChip: {
    backgroundColor: '#0f172a',
    borderWidth: 1,
    borderColor: '#334155',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    marginRight: 8,
  },
  langChipActive: {
    borderColor: '#10b981',
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
  },
  langText: {
    color: '#94a3b8',
    fontSize: 12,
    fontWeight: '600',
  },
  langTextActive: {
    color: '#34d399',
    fontWeight: '800',
  },
  dialectWarningBox: {
    backgroundColor: 'rgba(245, 158, 11, 0.12)',
    borderWidth: 1,
    borderColor: '#f59e0b',
    padding: 8,
    borderRadius: 8,
    marginBottom: 14,
  },
  dialectWarningText: {
    color: '#fde68a',
    fontSize: 10.5,
    lineHeight: 14,
  },
  voiceSection: {
    alignItems: 'center',
    marginVertical: 15,
  },
  micHeroButton: {
    width: 140,
    height: 140,
    borderRadius: 70,
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 8,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 10,
    borderWidth: 3,
  },
  micHeroIdle: {
    backgroundColor: '#0f172a',
    borderColor: '#10b981',
    shadowColor: '#10b981',
  },
  micHeroRecording: {
    backgroundColor: '#450a0a',
    borderColor: '#ef4444',
    shadowColor: '#ef4444',
  },
  micIcon: {
    fontSize: 38,
    marginBottom: 4,
  },
  micActionText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '800',
    textAlign: 'center',
  },
  micSubText: {
    color: '#94a3b8',
    fontSize: 9,
    textAlign: 'center',
    marginTop: 2,
  },
  recordingPulseBar: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 16,
    backgroundColor: 'rgba(239, 68, 68, 0.15)',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  redDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#ef4444',
  },
  recordingStatusText: {
    color: '#fca5a5',
    fontSize: 12,
    fontWeight: '700',
  },
  textSection: {
    marginTop: 10,
  },
  textArea: {
    backgroundColor: '#0f172a',
    borderWidth: 1.5,
    borderColor: '#334155',
    borderRadius: 12,
    color: '#ffffff',
    fontSize: 15,
    padding: 14,
    minHeight: 110,
    textAlignVertical: 'top',
    marginBottom: 16,
  },
  submitTextButton: {
    backgroundColor: '#10b981',
    minHeight: 64,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  submitTextButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '800',
  },
  loadingContainer: {
    marginTop: 20,
    alignItems: 'center',
    backgroundColor: '#0f172a',
    padding: 16,
    borderRadius: 12,
  },
  loadingText: {
    color: '#38bdf8',
    fontSize: 13,
    fontWeight: '600',
    marginTop: 8,
    textAlign: 'center',
  },
  reviewModalCard: {
    backgroundColor: '#0b1329',
    borderWidth: 2,
    borderColor: '#38bdf8',
    borderRadius: 14,
    padding: 20,
  },
  reviewHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  reviewTitle: {
    fontSize: 18,
    fontWeight: '900',
    color: '#ffffff',
  },
  confBadge: {
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
    borderWidth: 1,
    borderColor: '#10b981',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  confBadgeText: {
    color: '#34d399',
    fontSize: 10,
    fontWeight: '800',
  },
  reviewSub: {
    color: '#94a3b8',
    fontSize: 12,
    lineHeight: 16,
    marginBottom: 16,
  },
  transcriptBox: {
    backgroundColor: '#070d18',
    borderWidth: 1.5,
    borderColor: '#334155',
    borderRadius: 10,
    padding: 14,
    marginBottom: 12,
  },
  boxLabel: {
    color: '#64748b',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  transcriptText: {
    color: '#f8fafc',
    fontSize: 15,
    fontWeight: '600',
    lineHeight: 22,
  },
  transcriptTextEn: {
    color: '#e0f2fe',
    fontSize: 14,
    fontStyle: 'italic',
    lineHeight: 20,
  },
  clarificationBanner: {
    backgroundColor: 'rgba(245, 158, 11, 0.15)',
    borderWidth: 1.5,
    borderColor: '#f59e0b',
    borderRadius: 10,
    padding: 12,
    marginBottom: 16,
  },
  clarificationTitle: {
    color: '#fbbf24',
    fontSize: 11,
    fontWeight: '900',
    marginBottom: 4,
  },
  clarificationText: {
    color: '#fef3c7',
    fontSize: 13,
    fontWeight: '700',
    lineHeight: 18,
  },
  confirmButton: {
    backgroundColor: '#10b981',
    minHeight: 64,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 10,
  },
  confirmButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '900',
  },
  rerecordButton: {
    backgroundColor: '#1e293b',
    minHeight: 52,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  rerecordButtonText: {
    color: '#94a3b8',
    fontSize: 14,
    fontWeight: '700',
  },
});
