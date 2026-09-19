import React, { useEffect, useState } from 'react';
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
import { StepIndicator } from '../components/StepIndicator';
import {
  getNextQuestion,
  NextQuestionResponse,
  submitVerificationAnswer,
  transcribeAudioFile,
  Ticket,
} from '../services/api';
import { getApiBaseUrl } from '../services/config';
import { soundPlayer } from '../services/soundPlayer';

interface VerificationInterviewScreenProps {
  ticket: Ticket;
  onInterviewComplete: (finalTicket: Ticket) => void;
}

export const VerificationInterviewScreen: React.FC<VerificationInterviewScreenProps> = ({
  ticket,
  onInterviewComplete,
}) => {
  const [currentQuestion, setCurrentQuestion] = useState<NextQuestionResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [customAnswer, setCustomAnswer] = useState<string>('');
  const [audioSourceUri, setAudioSourceUri] = useState<string | null>(null);
  const [isPlayingAudio, setIsPlayingAudio] = useState<boolean>(false);

  // Voice recording state
  const audioRecorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [isTranscribing, setIsTranscribing] = useState<boolean>(false);
  const [recordedTranscript, setRecordedTranscript] = useState<string | null>(null);

  // Fetch next question from adaptive verification engine
  const fetchNextQ = async () => {
    try {
      setIsLoading(true);
      const data = await getNextQuestion(ticket.id, ticket.language);
      setCurrentQuestion(data);
      setIsLoading(false);

      if (data.done) {
        soundPlayer.stop();
        onInterviewComplete(ticket);
      } else if (data.question_audio_path) {
        const base = await getApiBaseUrl();
        const fullUrl = data.question_audio_path.startsWith('http')
          ? data.question_audio_path
          : `${base}${data.question_audio_path}`;
        setAudioSourceUri(fullUrl);
        // Auto-play audio aloud through phone speaker as soon as question loads
        playAudio(fullUrl);
      }
    } catch (err: any) {
      setIsLoading(false);
      Alert.alert('Verification Error', err.message || 'Could not fetch question.');
    }
  };

  useEffect(() => {
    fetchNextQ();
    return () => {
      soundPlayer.stop();
    };
  }, []);

  const playAudio = async (targetUri?: string) => {
    const uriToPlay = targetUri || audioSourceUri;
    if (!uriToPlay) return;
    await soundPlayer.playUrl(uriToPlay, (playing) => {
      setIsPlayingAudio(playing);
    });
  };

  // Start recording user's voice answer
  const startVoiceRecording = async () => {
    try {
      // 1. Stop audio playback first
      await soundPlayer.stop();
      setIsPlayingAudio(false);

      // 2. Request microphone permission
      const perm = await requestRecordingPermissionsAsync();
      if (!perm.granted) {
        Alert.alert(
          'Microphone Access Needed',
          'Please allow microphone access to speak your verification answer.'
        );
        return;
      }

      // 3. Switch audio session to recording mode
      await setAudioModeAsync({
        allowsRecording: true,
        playsInSilentMode: true,
      });

      await audioRecorder.prepareToRecordAsync();
      audioRecorder.record();
      setIsRecording(true);
      setRecordedTranscript(null);
    } catch (err: any) {
      Alert.alert('Microphone Error', err.message || 'Could not activate microphone.');
      setIsRecording(false);
    }
  };

  // Stop recording, transcribe speech with Whisper, and submit answer
  const stopVoiceRecordingAndSubmit = async () => {
    try {
      setIsRecording(false);
      setIsTranscribing(true);

      await audioRecorder.stop();
      const uri = audioRecorder.uri;

      if (!uri) {
        setIsTranscribing(false);
        throw new Error('No recorded voice audio found.');
      }

      // Transcribe via Whisper Small model on backend
      const res = await transcribeAudioFile(uri, ticket.language);
      const text = res?.transcript?.trim();
      const textEn = res?.transcript_en?.trim();

      if (!text) {
        setIsTranscribing(false);
        Alert.alert(
          'No Speech Detected',
          'Could not clearly hear your answer. Please tap Speak again and speak near the phone microphone, or tap an option below.'
        );
        return;
      }

      setRecordedTranscript(text);
      setIsTranscribing(false);

      // Automatically submit the voice answer
      await handleSelectOption(text, textEn);
    } catch (err: any) {
      setIsTranscribing(false);
      Alert.alert('Voice Submission Error', err.message || 'Failed to process voice response.');
    }
  };

  // Submit answer (from voice, chip click, or text input)
  const handleSelectOption = async (optionText: string, optionTextEn?: string) => {
    if (isSubmitting || !currentQuestion?.question) return;
    // Stop playing audio immediately on user answer
    await soundPlayer.stop();
    setIsPlayingAudio(false);

    try {
      setIsSubmitting(true);
      const updatedTicket = await submitVerificationAnswer(
        ticket.id,
        optionText,
        currentQuestion.question,
        optionTextEn
      );
      setIsSubmitting(false);

      // Check if all turns are done
      if (
        (currentQuestion.question_index ?? 0) + 1 >= currentQuestion.total_questions ||
        updatedTicket.verification_status !== 'pending'
      ) {
        onInterviewComplete(updatedTicket);
      } else {
        setRecordedTranscript(null);
        fetchNextQ();
      }
    } catch (err: any) {
      setIsSubmitting(false);
      Alert.alert('Error', err.message || 'Failed to submit answer.');
    }
  };

  return (
    <View style={styles.container}>
      <StepIndicator currentStep={3} />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* SOP Grounding Banner */}
        <View style={styles.sopBadge}>
          <Text style={styles.sopBadgeText}>
            📖 SOP: {currentQuestion?.sop_source || 'BSL Plant Safety Standard'}
          </Text>
        </View>

        {/* Turn indicator */}
        <Text style={styles.turnLabel}>
          Question {(currentQuestion?.question_index ?? 0) + 1} of{' '}
          {currentQuestion?.total_questions || 4}
        </Text>

        {isLoading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#38bdf8" />
            <Text style={styles.loadingText}>Synthesizing adaptive verification question...</Text>
          </View>
        ) : (
          <View>
            {/* Question Box */}
            <View style={styles.questionCard}>
              <Text style={styles.questionText}>{currentQuestion?.question}</Text>
              {audioSourceUri && (
                <TouchableOpacity
                  style={[styles.listenButton, isPlayingAudio && styles.listenButtonPlaying]}
                  onPress={() => playAudio(audioSourceUri)}
                >
                  <Text style={styles.listenButtonText}>
                    {isPlayingAudio ? '🔊 Playing Question Audio...' : '🔈 Replay Question Audio'}
                  </Text>
                </TouchableOpacity>
              )}
            </View>

            {/* Voice Input Section */}
            <View style={styles.voiceSection}>
              <Text style={styles.voiceSectionTitle}>
                {isRecording
                  ? '🔴 Listening to your voice... Speak now'
                  : isTranscribing
                  ? '⏳ Transcribing your answer...'
                  : '🎙️ Speak Your Answer in Native Language:'}
              </Text>

              {isTranscribing ? (
                <View style={styles.transcribingBox}>
                  <ActivityIndicator size="small" color="#38bdf8" />
                  <Text style={styles.transcribingText}>Processing speech with Whisper AI...</Text>
                </View>
              ) : (
                <TouchableOpacity
                  style={[
                    styles.voiceButton,
                    isRecording && styles.voiceButtonRecording,
                    isSubmitting && styles.voiceButtonDisabled,
                  ]}
                  onPress={isRecording ? stopVoiceRecordingAndSubmit : startVoiceRecording}
                  disabled={isSubmitting || isLoading}
                  activeOpacity={0.8}
                >
                  <Text style={styles.voiceIcon}>{isRecording ? '⏹️' : '🎙️'}</Text>
                  <View style={styles.voiceTextContainer}>
                    <Text
                      style={[
                        styles.voiceButtonTitle,
                        isRecording && styles.voiceButtonTitleRecording,
                      ]}
                    >
                      {isRecording ? 'Tap to Submit Voice Answer' : 'Tap to Speak Your Answer'}
                    </Text>
                    <Text style={styles.voiceButtonSub}>
                      {isRecording
                        ? 'Done speaking? Tap here to transcribe & verify'
                        : `Speaks directly in ${ticket.language === 'hi' ? 'Hindi (हिंदी)' : 'your language'}`}
                    </Text>
                  </View>
                </TouchableOpacity>
              )}

              {recordedTranscript && (
                <View style={styles.transcriptPreview}>
                  <Text style={styles.transcriptLabel}>Understood:</Text>
                  <Text style={styles.transcriptContent}>"{recordedTranscript}"</Text>
                </View>
              )}
            </View>

            {/* Divider */}
            <View style={styles.dividerRow}>
              <View style={styles.dividerLine} />
              <Text style={styles.dividerText}>OR SELECT QUICK FIELD OPTION</Text>
              <View style={styles.dividerLine} />
            </View>

            {/* Answer Options Grid */}
            {currentQuestion?.options.map((opt, idx) => (
              <TouchableOpacity
                key={idx}
                style={styles.optionCard}
                onPress={() => handleSelectOption(opt)}
                disabled={isSubmitting || isRecording}
                activeOpacity={0.7}
              >
                <View style={styles.optionIndex}>
                  <Text style={styles.optionIndexText}>{idx + 1}</Text>
                </View>
                <Text style={styles.optionText}>{opt}</Text>
              </TouchableOpacity>
            ))}

            {/* Custom typed answer */}
            <View style={styles.customAnswerRow}>
              <TextInput
                style={styles.customInput}
                placeholder="Or type specific detail..."
                placeholderTextColor="#64748b"
                value={customAnswer}
                onChangeText={setCustomAnswer}
                editable={!isRecording && !isSubmitting}
              />
              <TouchableOpacity
                style={styles.customSendButton}
                disabled={isRecording || isSubmitting}
                onPress={() => {
                  if (customAnswer.trim()) {
                    handleSelectOption(customAnswer.trim());
                    setCustomAnswer('');
                  }
                }}
              >
                <Text style={styles.customSendText}>Send</Text>
              </TouchableOpacity>
            </View>
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
  sopBadge: {
    backgroundColor: 'rgba(56, 189, 248, 0.15)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderColor: 'rgba(56, 189, 248, 0.3)',
    marginBottom: 8,
  },
  sopBadgeText: {
    color: '#38bdf8',
    fontSize: 11,
    fontWeight: '700',
  },
  turnLabel: {
    color: '#94a3b8',
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 12,
  },
  loadingContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 50,
  },
  loadingText: {
    color: '#94a3b8',
    marginTop: 12,
    fontSize: 13,
  },
  questionCard: {
    backgroundColor: '#0f172a',
    borderRadius: 14,
    padding: 18,
    borderWidth: 1,
    borderColor: '#1e293b',
    marginBottom: 18,
  },
  questionText: {
    color: '#ffffff',
    fontSize: 17,
    fontWeight: '700',
    lineHeight: 24,
    marginBottom: 12,
  },
  listenButton: {
    backgroundColor: '#1e293b',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 8,
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderColor: '#334155',
  },
  listenButtonPlaying: {
    backgroundColor: 'rgba(56, 189, 248, 0.2)',
    borderColor: '#38bdf8',
  },
  listenButtonText: {
    color: '#38bdf8',
    fontSize: 12,
    fontWeight: '600',
  },
  voiceSection: {
    backgroundColor: '#0b1329',
    borderRadius: 14,
    padding: 14,
    borderWidth: 1.5,
    borderColor: 'rgba(56, 189, 248, 0.3)',
    marginBottom: 18,
  },
  voiceSectionTitle: {
    color: '#38bdf8',
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  voiceButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(56, 189, 248, 0.1)',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1.5,
    borderColor: '#38bdf8',
  },
  voiceButtonRecording: {
    backgroundColor: 'rgba(239, 68, 68, 0.15)',
    borderColor: '#ef4444',
  },
  voiceButtonDisabled: {
    opacity: 0.5,
  },
  voiceIcon: {
    fontSize: 26,
    marginRight: 12,
  },
  voiceTextContainer: {
    flex: 1,
  },
  voiceButtonTitle: {
    color: '#38bdf8',
    fontSize: 15,
    fontWeight: '700',
    marginBottom: 2,
  },
  voiceButtonTitleRecording: {
    color: '#f87171',
  },
  voiceButtonSub: {
    color: '#94a3b8',
    fontSize: 11,
  },
  transcribingBox: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    backgroundColor: '#0f172a',
    borderRadius: 12,
  },
  transcribingText: {
    color: '#38bdf8',
    fontSize: 13,
    fontWeight: '600',
    marginLeft: 10,
  },
  transcriptPreview: {
    marginTop: 10,
    padding: 10,
    backgroundColor: '#070d18',
    borderRadius: 8,
    borderLeftWidth: 3,
    borderLeftColor: '#38bdf8',
  },
  transcriptLabel: {
    color: '#94a3b8',
    fontSize: 11,
    fontWeight: '600',
  },
  transcriptContent: {
    color: '#f8fafc',
    fontSize: 13,
    fontStyle: 'italic',
    marginTop: 2,
  },
  dividerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#1e293b',
  },
  dividerText: {
    color: '#64748b',
    fontSize: 10,
    fontWeight: '700',
    paddingHorizontal: 10,
    letterSpacing: 0.5,
  },
  optionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0c1626',
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1.5,
    borderColor: '#1e293b',
  },
  optionIndex: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: '#1e293b',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  optionIndexText: {
    color: '#38bdf8',
    fontSize: 12,
    fontWeight: '700',
  },
  optionText: {
    color: '#f1f5f9',
    fontSize: 14,
    fontWeight: '600',
    flex: 1,
  },
  customAnswerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 10,
  },
  customInput: {
    flex: 1,
    backgroundColor: '#0f172a',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: '#ffffff',
    fontSize: 13,
    borderWidth: 1,
    borderColor: '#1e293b',
    marginRight: 8,
  },
  customSendButton: {
    backgroundColor: '#2563eb',
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 10,
  },
  customSendText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '700',
  },
});
