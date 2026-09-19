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

interface IncidentRecorderScreenProps {
  reportType: 'emergency' | 'suspected';
  onIncidentCreated: (ticket: Ticket) => void;
  onBack: () => void;
}

export const IncidentRecorderScreen: React.FC<IncidentRecorderScreenProps> = ({
  reportType,
  onIncidentCreated,
  onBack,
}) => {
  const [mode, setMode] = useState<'voice' | 'text'>('voice');
  const [selectedLanguage, setSelectedLanguage] = useState<string>('hi');
  const [textInput, setTextInput] = useState<string>('');
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string>('');

  // Use the modern SDK 57 expo-audio recorder hook
  const audioRecorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);

  // Start voice recording
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

      // Configure iOS audio session to permit microphone recording
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

  // Stop recording & upload to backend
  const stopRecordingAndSubmit = async () => {
    try {
      setIsRecording(false);
      setIsLoading(true);
      setStatusMessage('Processing audio with Whisper Small...');

      await audioRecorder.stop();
      const uri = audioRecorder.uri;

      if (!uri) {
        throw new Error('No recorded audio file found.');
      }

      const ticket = await createIncidentFromAudio(uri, reportType, selectedLanguage);
      setIsLoading(false);
      onIncidentCreated(ticket);
    } catch (err: any) {
      setIsLoading(false);
      Alert.alert('Upload Failed', err.message || 'Could not send audio report to plant server.');
    }
  };

  // Submit typed text incident
  const submitText = async () => {
    if (!textInput.trim()) {
      Alert.alert('Required', 'Please type a description of the safety observation.');
      return;
    }
    try {
      setIsLoading(true);
      setStatusMessage('Submitting incident notice...');
      const ticket = await createIncidentFromText({
        report_type: reportType,
        incident_description: textInput.trim(),
        language: selectedLanguage,
      });
      setIsLoading(false);
      onIncidentCreated(ticket);
    } catch (err: any) {
      setIsLoading(false);
      Alert.alert('Submission Failed', err.message || 'Failed to submit report.');
    }
  };

  return (
    <View style={styles.container}>
      <StepIndicator currentStep={1} />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Plant header */}
        <View style={styles.topBar}>
          <TouchableOpacity onPress={onBack} style={styles.backButton}>
            <Text style={styles.backButtonText}>‹ Back</Text>
          </TouchableOpacity>
          <View style={styles.typeBadge}>
            <Text style={styles.typeBadgeText}>
              {reportType === 'emergency' ? '🚨 EMERGENCY' : '⚠️ INCIDENT INTAKE'}
            </Text>
          </View>
        </View>

        <Text style={styles.screenTitle}>
          {reportType === 'emergency' ? 'Emergency Incident Notice' : 'Describe What Happened'}
        </Text>
        <Text style={styles.screenSubtitle}>
          Voice intake automatically transcribes Hindi, Bengali, Tamil, Telugu, English & more.
        </Text>

        {/* Mode Switcher */}
        <View style={styles.tabContainer}>
          <TouchableOpacity
            style={[styles.tabButton, mode === 'voice' && styles.tabButtonActive]}
            onPress={() => setMode('voice')}
          >
            <Text style={[styles.tabText, mode === 'voice' && styles.tabTextActive]}>
              🎙️ Voice Report
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
        <Text style={styles.sectionLabel}>Spoken Language Preference:</Text>
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

        {/* Voice Mode */}
        {mode === 'voice' && (
          <View style={styles.voiceSection}>
            <TouchableOpacity
              style={[
                styles.micHeroButton,
                isRecording ? styles.micHeroRecording : styles.micHeroIdle,
              ]}
              onPress={isRecording ? stopRecordingAndSubmit : startRecording}
              disabled={isLoading}
              activeOpacity={0.8}
            >
              <Text style={styles.micIcon}>{isRecording ? '⏹️' : '🎙️'}</Text>
              <Text style={styles.micActionText}>
                {isRecording ? 'Tap to Finish Speaking' : 'Tap to Speak'}
              </Text>
              <Text style={styles.micSubText}>
                {isRecording ? 'Listening now...' : 'Tap once & speak clearly'}
              </Text>
            </TouchableOpacity>

            {isRecording && (
              <View style={styles.recordingPulseBar}>
                <View style={styles.redDot} />
                <Text style={styles.recordingStatusText}>Recording in progress...</Text>
              </View>
            )}
          </View>
        )}

        {/* Text Mode */}
        {mode === 'text' && (
          <View style={styles.textSection}>
            <TextInput
              style={styles.textArea}
              placeholder="E.g., Blast furnace 1 ke paas gas leak ki gandh aa rahi hai, pipeline me hissing sunayi di..."
              placeholderTextColor="#64748b"
              multiline
              numberOfLines={4}
              value={textInput}
              onChangeText={setTextInput}
              editable={!isLoading}
            />
            <TouchableOpacity
              style={styles.submitButton}
              onPress={submitText}
              disabled={isLoading}
            >
              <Text style={styles.submitButtonText}>Submit Incident Notice ➔</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Loading Spinner / Status message */}
        {isLoading && (
          <View style={styles.loadingBanner}>
            <ActivityIndicator size="small" color="#38bdf8" />
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
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  backButton: {
    paddingVertical: 6,
    paddingHorizontal: 10,
  },
  backButtonText: {
    color: '#94a3b8',
    fontSize: 15,
    fontWeight: '600',
  },
  typeBadge: {
    backgroundColor: '#1e293b',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  typeBadgeText: {
    color: '#38bdf8',
    fontSize: 11,
    fontWeight: '700',
  },
  screenTitle: {
    color: '#ffffff',
    fontSize: 22,
    fontWeight: '800',
    marginBottom: 6,
  },
  screenSubtitle: {
    color: '#94a3b8',
    fontSize: 13,
    marginBottom: 16,
    lineHeight: 18,
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
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  tabButtonActive: {
    backgroundColor: '#2563eb',
  },
  tabText: {
    color: '#94a3b8',
    fontSize: 13,
    fontWeight: '600',
  },
  tabTextActive: {
    color: '#ffffff',
    fontWeight: '700',
  },
  sectionLabel: {
    color: '#cbd5e1',
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 8,
  },
  langScroll: {
    marginBottom: 20,
  },
  langChip: {
    backgroundColor: '#0f172a',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16,
    marginRight: 8,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  langChipActive: {
    backgroundColor: 'rgba(56, 189, 248, 0.2)',
    borderColor: '#38bdf8',
  },
  langText: {
    color: '#94a3b8',
    fontSize: 12,
    fontWeight: '600',
  },
  langTextActive: {
    color: '#38bdf8',
    fontWeight: '700',
  },
  voiceSection: {
    alignItems: 'center',
    marginVertical: 15,
  },
  micHeroButton: {
    width: 170,
    height: 170,
    borderRadius: 85,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#2563eb',
    shadowOpacity: 0.5,
    shadowRadius: 20,
    elevation: 8,
  },
  micHeroIdle: {
    backgroundColor: '#2563eb',
    borderWidth: 4,
    borderColor: '#60a5fa',
  },
  micHeroRecording: {
    backgroundColor: '#dc2626',
    borderWidth: 4,
    borderColor: '#f87171',
  },
  micIcon: {
    fontSize: 44,
    marginBottom: 6,
  },
  micActionText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '800',
  },
  micSubText: {
    color: 'rgba(255,255,255,0.8)',
    fontSize: 11,
    marginTop: 2,
  },
  recordingPulseBar: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 18,
    backgroundColor: 'rgba(239, 68, 68, 0.15)',
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 14,
  },
  redDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#ef4444',
    marginRight: 8,
  },
  recordingStatusText: {
    color: '#f87171',
    fontSize: 12,
    fontWeight: '700',
  },
  textSection: {
    marginTop: 8,
  },
  textArea: {
    backgroundColor: '#0f172a',
    borderRadius: 12,
    padding: 14,
    color: '#ffffff',
    fontSize: 14,
    minHeight: 110,
    textAlignVertical: 'top',
    borderWidth: 1,
    borderColor: '#1e293b',
    marginBottom: 14,
  },
  submitButton: {
    backgroundColor: '#2563eb',
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  submitButtonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '700',
  },
  loadingBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(15, 23, 42, 0.9)',
    padding: 12,
    borderRadius: 10,
    marginTop: 20,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  loadingText: {
    color: '#38bdf8',
    fontSize: 12,
    fontWeight: '600',
    marginLeft: 8,
  },
});
