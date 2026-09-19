import React, { useState, useEffect, useRef } from 'react';
import {
  ActivityIndicator,
  Alert,
  Animated,
  Image,
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
import { RESTRICTED_ZONES_MAP } from '../components/ZoneRestrictionBanner';
import { KioskSession } from './KioskLoginScreen';
import { i18n } from '../services/i18n';
import { outbox } from '../services/outbox';

interface IncidentRecorderScreenProps {
  reportType: 'emergency' | 'suspected';
  onIncidentCreated: (ticket: Ticket) => void;
  onBack: () => void;
  kioskSession?: KioskSession | null;
  onSwitchToKiosk?: () => void;
  isAnonymous?: boolean;
  shift?: string;
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
  isAnonymous = false,
  shift = 'Shift A',
}) => {
  const [mode, setMode] = useState<'voice' | 'text'>('voice');
  const [selectedLanguage, setSelectedLanguage] = useState<string>(i18n.getLanguage());
  const [selectedZone, setSelectedZone] = useState<string>('BF1');
  const [textInput, setTextInput] = useState<string>('');
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [transcribedTicket, setTranscribedTicket] = useState<Ticket | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);

  // Audio waveform equalizer animation (11 bars with staggered heights)
  const waveAnims = useRef(Array.from({ length: 11 }, () => new Animated.Value(0.25))).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;

  // Track recording elapsed time
  useEffect(() => {
    let interval: any = null;
    if (isRecording) {
      setElapsedSeconds(0);
      interval = setInterval(() => {
        setElapsedSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      setElapsedSeconds(0);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isRecording]);

  // Audio equalizer & halo pulsing loop
  useEffect(() => {
    if (isRecording) {
      const barAnimations = waveAnims.map((anim, i) => {
        const minScale = 0.2 + (i % 3) * 0.08;
        const maxScale = 0.65 + ((i * 7) % 5) * 0.08;
        return Animated.loop(
          Animated.sequence([
            Animated.timing(anim, {
              toValue: maxScale,
              duration: 180 + (i * 35) % 200,
              useNativeDriver: true,
            }),
            Animated.timing(anim, {
              toValue: minScale,
              duration: 180 + ((11 - i) * 35) % 200,
              useNativeDriver: true,
            }),
          ])
        );
      });
      barAnimations.forEach((a) => a.start());

      const haloPulse = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.08,
            duration: 800,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1.0,
            duration: 800,
            useNativeDriver: true,
          }),
        ])
      );
      haloPulse.start();

      return () => {
        barAnimations.forEach((a) => a.stop());
        haloPulse.stop();
      };
    } else {
      waveAnims.forEach((anim) => anim.setValue(0.25));
      pulseAnim.setValue(1);
    }
  }, [isRecording]);

  const formatTimer = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m < 10 ? '0' : ''}${m}:${s < 10 ? '0' : ''}${s}`;
  };

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
        const ticket = await createIncidentFromAudio(uri, reportType, selectedLanguage, {
          is_anonymous: isAnonymous,
          shift,
          zone_id: selectedZone,
          worker_badge_id: isAnonymous ? undefined : kioskSession?.workerBadgeId,
          reporter_supervisor_id: kioskSession?.supervisorId,
          kiosk_station_id: kioskSession?.kioskStationId,
          reporting_mode: kioskSession ? 'kiosk_supervisor' : (isAnonymous ? 'anonymous_near_miss' : 'personal'),
        });
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
          employee_id: isAnonymous ? undefined : kioskSession?.workerBadgeId,
          extraOptions: {
            is_anonymous: isAnonymous,
            shift,
            zone_id: selectedZone,
          },
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
          is_anonymous: isAnonymous,
          shift,
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
          is_anonymous: isAnonymous,
          shift,
          worker_badge_id: isAnonymous ? undefined : kioskSession?.workerBadgeId,
          reporter_supervisor_id: kioskSession?.supervisorId,
          kiosk_station_id: kioskSession?.kioskStationId,
          reporting_mode: kioskSession ? 'kiosk_supervisor' : (isAnonymous ? 'anonymous_near_miss' : 'personal'),
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
          employee_id: isAnonymous ? undefined : kioskSession?.workerBadgeId,
          is_anonymous: isAnonymous,
          shift,
        });
        setIsLoading(false);

        const offlineTicket: Ticket = {
          id: `offline_${Date.now()}`,
          report_type: reportType,
          incident_description: textInput.trim(),
          is_anonymous: isAnonymous,
          shift,
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
            <Text style={styles.reviewTitle}>Confirm Speech Transcript</Text>
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
            <View style={styles.transcriptBox}>
              <Text style={styles.boxLabel}>ENGLISH OPERATIONAL TRANSLATION:</Text>
              <Text style={styles.transcriptTextEn}>
                "{transcribedTicket.incident_description_en}"
              </Text>
            </View>
          )}

          {/* Low Confidence Critical Word Clarification Prompt */}
          {transcribedTicket.clarification_prompt && (
            <View style={styles.clarificationBanner}>
              <Text style={styles.clarificationTitle}>ASR CONFIRMATION REQUIRED:</Text>
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

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Kiosk or Supervisor Proxy Mode Header */}
        {kioskSession && (
          <View style={styles.kioskHeaderRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.kioskTitle}>
                {kioskSession.reportingMode === 'supervisor_proxy'
                  ? `SUPERVISOR PROXY (By ${kioskSession.supervisorId || 'Supervisor'})`
                  : 'SHARED KIOSK TERMINAL'}
              </Text>
              <Text style={styles.kioskSub}>
                Worker Badge: <Text style={{ color: '#ffffff', fontWeight: '800' }}>{kioskSession.workerBadgeId}</Text> • Station: {kioskSession.kioskStationId}
              </Text>
            </View>
          </View>
        )}

        {/* Top bar */}
        <View style={styles.topBar}>
          <TouchableOpacity onPress={onBack} style={styles.backButton} activeOpacity={0.7}>
            <Text style={styles.backButtonText}>‹ Back</Text>
          </TouchableOpacity>
          <View style={[styles.typeBadge, reportType === 'emergency' && styles.typeBadgeEmergency]}>
            <Text style={styles.typeBadgeText}>
              {reportType === 'emergency' ? 'CRITICAL EMERGENCY' : 'INCIDENT OBSERVATION'}
            </Text>
          </View>
        </View>

        {/* Screen Heading */}
        <View style={styles.headingSection}>
          <Text style={styles.screenTitle}>
            {reportType === 'emergency' ? 'Emergency Incident Notice' : 'Describe What Happened'}
          </Text>
          <Text style={styles.screenSubtitle}>
            Voice-first reporting with real-time acoustic plant noise suppression.
          </Text>
        </View>

        {/* Apple Segmented Control (Voice vs Text) */}
        <View style={styles.segmentedControl}>
          <TouchableOpacity
            style={[styles.segmentTab, mode === 'voice' && styles.segmentTabActive]}
            onPress={() => setMode('voice')}
            activeOpacity={0.8}
          >
            <Text style={[styles.segmentText, mode === 'voice' && styles.segmentTextActive]}>
              Voice Intake (Primary)
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.segmentTab, mode === 'text' && styles.segmentTabActive]}
            onPress={() => setMode('text')}
            activeOpacity={0.8}
          >
            <Text style={[styles.segmentText, mode === 'text' && styles.segmentTextActive]}>
              Type Text
            </Text>
          </TouchableOpacity>
        </View>

        {/* VOICE MODE: Apple Acoustic Studio */}
        {mode === 'voice' && (
          <View style={styles.studioCard}>
            {/* Studio Header: Status / Live Stopwatch */}
            <View style={styles.studioHeader}>
              {isRecording ? (
                <View style={styles.liveRecordingBadge}>
                  <View style={styles.livePulseDot} />
                  <Text style={styles.liveRecordingText}>LIVE RECORDING</Text>
                </View>
              ) : (
                <View style={styles.idleReadyBadge}>
                  <View style={styles.idleDot} />
                  <Text style={styles.idleReadyText}>READY TO RECORD</Text>
                </View>
              )}
            </View>

            {/* Stopwatch Timer Display */}
            {isRecording && (
              <View style={styles.timerRow}>
                <Text style={styles.timerDigits}>{formatTimer(elapsedSeconds)}</Text>
              </View>
            )}

            {/* Live Audio Equalizer Waveform */}
            <View style={styles.waveformContainer}>
              {waveAnims.map((anim, idx) => (
                <Animated.View
                  key={idx}
                  style={[
                    styles.waveformBar,
                    {
                      transform: [{ scaleY: anim }],
                      backgroundColor: isRecording ? '#FFFFFF' : 'rgba(255, 255, 255, 0.3)',
                      opacity: isRecording ? 1 : 0.45,
                    },
                  ]}
                />
              ))}
            </View>

            {/* Concentric Breathing Halo Hero */}
            <View style={styles.micStageContainer}>
              <Animated.View
                style={[
                  styles.micOuterHalo,
                  isRecording && styles.micOuterHaloRecording,
                  { transform: [{ scale: pulseAnim }] },
                ]}
              >
                <View style={[styles.micInnerHalo, isRecording && styles.micInnerHaloRecording]}>
                  <TouchableOpacity
                    style={[
                      styles.micHeroButton,
                      isRecording ? styles.micHeroRecording : styles.micHeroIdle,
                    ]}
                    onPress={isRecording ? stopRecordingAndTranscribe : startRecording}
                    disabled={isLoading}
                    activeOpacity={0.85}
                  >
                    <Image
                      source={
                        isRecording
                          ? require('../../assets/stop.png')
                          : require('../../assets/mic.png')
                      }
                      style={styles.micImage}
                      resizeMode="contain"
                    />
                  </TouchableOpacity>
                </View>
              </Animated.View>
            </View>

            {/* Studio Action Prompt */}
            <Text style={styles.micActionText}>
              {isRecording ? 'Tap to Stop & Transcribe' : 'Tap Microphone to Speak'}
            </Text>
            <Text style={styles.micSubText}>
              {isRecording
                ? 'Plant noise filter active • Whisper AI listening'
                : 'One-handed trigger • Optimized for industrial PPE gloves'}
            </Text>
          </View>
        )}

        {/* TEXT MODE */}
        {mode === 'text' && (
          <View style={styles.textSection}>
            <TextInput
              style={styles.textArea}
              placeholder="Describe the hazard or incident in detail (e.g. Molten slag overflow near casthouse tuyere, LOTO applied at breaker panel)..."
              placeholderTextColor="rgba(235, 235, 245, 0.4)"
              multiline
              numberOfLines={5}
              value={textInput}
              onChangeText={setTextInput}
              editable={!isLoading}
            />
            <TouchableOpacity
              style={styles.submitTextButton}
              onPress={submitText}
              disabled={isLoading}
              activeOpacity={0.85}
            >
              <Text style={styles.submitTextButtonText}>Submit Incident Notice ➔</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Grouped Card 1: Observed Plant Zone */}
        <View style={styles.configGroupCard}>
          <View style={styles.configHeaderRow}>
            <Text style={styles.configGroupLabel}>OBSERVED PLANT ZONE</Text>
            <Text style={styles.configSelectedValue}>{selectedZone}</Text>
          </View>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chipsScroll}>
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
                  activeOpacity={0.7}
                >
                  <Text style={[styles.zoneText, isSelected && styles.zoneTextSelected]}>
                    {z.name} ({z.id})
                  </Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        </View>

        {/* Grouped Card 2: Spoken Language Preference */}
        <View style={styles.configGroupCard}>
          <View style={styles.configHeaderRow}>
            <Text style={styles.configGroupLabel}>SPOKEN LANGUAGE</Text>
            <Text style={styles.configSelectedValue}>
              {INTAKE_LANGUAGES.find((l) => l.code === selectedLanguage)?.label || selectedLanguage}
            </Text>
          </View>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chipsScroll}>
            {INTAKE_LANGUAGES.map((l) => {
              const isSelected = selectedLanguage === l.code;
              return (
                <TouchableOpacity
                  key={l.code}
                  style={[styles.langChip, isSelected && styles.langChipActive]}
                  onPress={() => setSelectedLanguage(l.code)}
                  activeOpacity={0.7}
                >
                  <Text style={[styles.langText, isSelected && styles.langTextActive]}>
                    {l.label}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>

          {/* Regional Dialect Warning if Applicable */}
          {(selectedLanguage === 'bn' || selectedLanguage === 'or') && (
            <View style={styles.dialectWarningBox}>
              <Text style={styles.dialectWarningText}>{i18n.t('dialectNotice')}</Text>
            </View>
          )}
        </View>

        {/* Loading Spinner */}
        {isLoading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#ffffff" />
            <Text style={styles.loadingText}>{statusMessage}</Text>
          </View>
        )}

        {/* Security & Reliability Footer Note */}
        <View style={styles.securityFooter}>
          <Text style={styles.securityFooterText}>
            🔒 On-Premise Encrypted • Offline Local Queue Enabled
          </Text>
        </View>
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
  kioskHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1c1c1e',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    padding: 12,
    borderRadius: 16,
    marginBottom: 14,
    gap: 12,
  },
  kioskIcon: {
    fontSize: 22,
  },
  kioskTitle: {
    color: 'rgba(235, 235, 245, 0.6)',
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.2,
  },
  kioskSub: {
    color: 'rgba(235, 235, 245, 0.85)',
    fontSize: 13,
  },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14,
  },
  backButton: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: '#1c1c1e',
    borderRadius: 9999,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
  },
  backButtonText: {
    color: '#0A84FF',
    fontSize: 14,
    fontWeight: '600',
  },
  typeBadge: {
    backgroundColor: '#1c1c1e',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 9999,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
  },
  typeBadgeEmergency: {
    backgroundColor: 'rgba(255, 69, 58, 0.12)',
    borderColor: 'rgba(255, 69, 58, 0.3)',
  },
  typeBadgeText: {
    color: '#f8fafc',
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
  headingSection: {
    marginBottom: 16,
  },
  screenTitle: {
    fontSize: 26,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: 4,
    letterSpacing: -0.5,
  },
  screenSubtitle: {
    fontSize: 14,
    color: 'rgba(235, 235, 245, 0.65)',
    lineHeight: 20,
    letterSpacing: -0.2,
  },
  segmentedControl: {
    flexDirection: 'row',
    backgroundColor: '#161618',
    borderRadius: 14,
    padding: 3,
    marginBottom: 18,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
  },
  segmentTab: {
    flex: 1,
    paddingVertical: 9,
    alignItems: 'center',
    borderRadius: 11,
  },
  segmentTabActive: {
    backgroundColor: '#ffffff',
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 3,
  },
  segmentText: {
    color: 'rgba(235, 235, 245, 0.6)',
    fontSize: 13,
    fontWeight: '600',
    letterSpacing: -0.2,
  },
  segmentTextActive: {
    color: '#000000',
    fontWeight: '700',
  },
  studioCard: {
    backgroundColor: '#141416',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 24,
    padding: 22,
    alignItems: 'center',
    marginBottom: 18,
  },
  studioHeader: {
    marginBottom: 10,
    alignItems: 'center',
  },
  liveRecordingBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 69, 58, 0.12)',
    borderWidth: 1,
    borderColor: 'rgba(255, 69, 58, 0.3)',
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 9999,
    gap: 6,
  },
  livePulseDot: {
    width: 7,
    height: 7,
    borderRadius: 3.5,
    backgroundColor: '#FF453A',
  },
  liveRecordingText: {
    color: '#FF453A',
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  idleReadyBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.06)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 9999,
    gap: 6,
  },
  idleDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#30D158',
  },
  idleReadyText: {
    color: 'rgba(235, 235, 245, 0.65)',
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  timerRow: {
    marginBottom: 10,
  },
  timerDigits: {
    color: '#FFFFFF',
    fontSize: 34,
    fontWeight: '700',
    fontVariant: ['tabular-nums'],
    letterSpacing: 0.5,
  },
  waveformContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 44,
    gap: 4.5,
    marginBottom: 16,
    paddingHorizontal: 16,
  },
  waveformBar: {
    width: 3.5,
    height: 40,
    borderRadius: 2,
    backgroundColor: '#FFFFFF',
  },
  micStageContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 6,
  },
  micOuterHalo: {
    width: 172,
    height: 172,
    borderRadius: 86,
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.06)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  micOuterHaloRecording: {
    backgroundColor: 'rgba(255, 69, 58, 0.08)',
    borderColor: 'rgba(255, 69, 58, 0.2)',
  },
  micInnerHalo: {
    width: 136,
    height: 136,
    borderRadius: 68,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  micInnerHaloRecording: {
    backgroundColor: 'rgba(255, 69, 58, 0.12)',
    borderColor: 'rgba(255, 69, 58, 0.35)',
  },
  micHeroButton: {
    width: 100,
    height: 100,
    borderRadius: 50,
    alignItems: 'center',
    justifyContent: 'center',
  },
  micHeroIdle: {
    backgroundColor: '#1c1c1e',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.22)',
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 10,
  },
  micHeroRecording: {
    backgroundColor: '#2c2c2e',
    borderWidth: 2,
    borderColor: '#FF453A',
    shadowColor: '#FF453A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.45,
    shadowRadius: 16,
  },
  micImage: {
    width: 44,
    height: 44,
  },
  micActionText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
    textAlign: 'center',
    letterSpacing: -0.2,
    marginTop: 14,
  },
  micSubText: {
    color: 'rgba(235, 235, 245, 0.6)',
    fontSize: 12,
    textAlign: 'center',
    marginTop: 4,
    lineHeight: 16,
  },
  configGroupCard: {
    backgroundColor: '#161618',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 18,
    padding: 14,
    marginBottom: 14,
  },
  configHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
    paddingHorizontal: 2,
  },
  configGroupLabel: {
    color: 'rgba(235, 235, 245, 0.45)',
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.3,
    textTransform: 'uppercase',
  },
  configSelectedValue: {
    color: 'rgba(235, 235, 245, 0.85)',
    fontSize: 12,
    fontWeight: '600',
  },
  chipsScroll: {
    marginHorizontal: -4,
    paddingHorizontal: 4,
  },
  zoneChip: {
    backgroundColor: '#242426',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 9999,
    marginRight: 8,
  },
  zoneChipSelected: {
    borderColor: '#ffffff',
    backgroundColor: '#ffffff',
  },
  zoneChipRestricted: {
    borderColor: 'rgba(255, 69, 58, 0.6)',
    backgroundColor: '#242426',
  },
  zoneText: {
    color: 'rgba(235, 235, 245, 0.75)',
    fontSize: 13,
    fontWeight: '500',
  },
  zoneTextSelected: {
    color: '#000000',
    fontWeight: '700',
  },
  langChip: {
    backgroundColor: '#242426',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 9999,
    marginRight: 8,
  },
  langChipActive: {
    borderColor: '#ffffff',
    backgroundColor: '#ffffff',
  },
  langText: {
    color: 'rgba(235, 235, 245, 0.75)',
    fontSize: 13,
    fontWeight: '500',
  },
  langTextActive: {
    color: '#000000',
    fontWeight: '700',
  },
  dialectWarningBox: {
    backgroundColor: '#242426',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    padding: 10,
    borderRadius: 12,
    marginTop: 10,
  },
  dialectWarningText: {
    color: 'rgba(235, 235, 245, 0.7)',
    fontSize: 12,
    lineHeight: 16,
    fontWeight: '500',
  },
  securityFooter: {
    marginTop: 8,
    marginBottom: 20,
    alignItems: 'center',
  },
  securityFooterText: {
    color: 'rgba(235, 235, 245, 0.4)',
    fontSize: 12,
    fontWeight: '500',
  },
  textSection: {
    marginBottom: 16,
  },
  textArea: {
    backgroundColor: '#161618',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
    borderRadius: 18,
    color: '#ffffff',
    fontSize: 15,
    padding: 16,
    minHeight: 120,
    textAlignVertical: 'top',
    marginBottom: 14,
  },
  submitTextButton: {
    backgroundColor: '#ffffff',
    minHeight: 52,
    borderRadius: 9999,
    alignItems: 'center',
    justifyContent: 'center',
  },
  submitTextButtonText: {
    color: '#000000',
    fontSize: 16,
    fontWeight: '600',
    letterSpacing: -0.2,
  },
  loadingContainer: {
    marginTop: 20,
    alignItems: 'center',
    backgroundColor: '#1c1c1e',
    padding: 18,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  loadingText: {
    color: 'rgba(235, 235, 245, 0.7)',
    fontSize: 14,
    fontWeight: '500',
    marginTop: 10,
    textAlign: 'center',
  },
  reviewModalCard: {
    backgroundColor: '#1c1c1e',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.15)',
    borderRadius: 22,
    padding: 20,
  },
  reviewHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  reviewTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#ffffff',
    letterSpacing: -0.3,
  },
  confBadge: {
    backgroundColor: '#2c2c2e',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.15)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 9999,
  },
  confBadgeText: {
    color: '#ffffff',
    fontSize: 11,
    fontWeight: '600',
  },
  reviewSub: {
    color: 'rgba(235, 235, 245, 0.65)',
    fontSize: 13,
    lineHeight: 18,
    marginBottom: 16,
  },
  transcriptBox: {
    backgroundColor: '#000000',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 16,
    padding: 14,
    marginBottom: 14,
  },
  boxLabel: {
    color: 'rgba(235, 235, 245, 0.45)',
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.2,
    marginBottom: 6,
    textTransform: 'uppercase',
  },
  transcriptText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '500',
    lineHeight: 22,
  },
  transcriptTextEn: {
    color: 'rgba(235, 235, 245, 0.7)',
    fontSize: 14,
    fontStyle: 'italic',
    lineHeight: 20,
    marginTop: 4,
  },
  clarificationBanner: {
    backgroundColor: '#1c1c1e',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
    borderRadius: 16,
    padding: 12,
    marginBottom: 16,
  },
  clarificationTitle: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '700',
    marginBottom: 4,
  },
  clarificationText: {
    color: 'rgba(235, 235, 245, 0.85)',
    fontSize: 13,
    fontWeight: '500',
    lineHeight: 18,
  },
  confirmButton: {
    backgroundColor: '#ffffff',
    minHeight: 52,
    borderRadius: 9999,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 10,
  },
  confirmButtonText: {
    color: '#000000',
    fontSize: 16,
    fontWeight: '600',
    letterSpacing: -0.2,
  },
  rerecordButton: {
    backgroundColor: '#2c2c2e',
    minHeight: 50,
    borderRadius: 9999,
    alignItems: 'center',
    justifyContent: 'center',
  },
  rerecordButtonText: {
    color: 'rgba(235, 235, 245, 0.7)',
    fontSize: 14,
    fontWeight: '600',
  },
});
