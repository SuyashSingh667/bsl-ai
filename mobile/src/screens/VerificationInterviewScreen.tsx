import React, { useEffect, useRef, useState } from 'react';
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
import * as FileSystem from 'expo-file-system/legacy';
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

  // Auto-mic hands-free mode (default ON)
  const [autoMicEnabled, setAutoMicEnabled] = useState<boolean>(true);
  const autoMicRef = useRef<boolean>(true);
  autoMicRef.current = autoMicEnabled;

  // Voice recording state
  const audioRecorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [isTranscribing, setIsTranscribing] = useState<boolean>(false);
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);
  const [recordedTranscript, setRecordedTranscript] = useState<string | null>(null);

  // Synchronization refs
  const isRecordingRef = useRef<boolean>(false);
  const isSubmittingRef = useRef<boolean>(false);
  const elapsedTimerRef = useRef<any>(null);
  const autoStartTimerRef = useRef<any>(null);

  isRecordingRef.current = isRecording;
  isSubmittingRef.current = isSubmitting;

  const clearTimers = () => {
    if (elapsedTimerRef.current) {
      clearInterval(elapsedTimerRef.current);
      elapsedTimerRef.current = null;
    }
    if (autoStartTimerRef.current) {
      clearTimeout(autoStartTimerRef.current);
      autoStartTimerRef.current = null;
    }
  };

  // Fetch next question from adaptive verification engine
  const fetchNextQ = async () => {
    clearTimers();
    try {
      setIsLoading(true);
      const data = await getNextQuestion(ticket.id, ticket.language);
      setCurrentQuestion(data);
      setIsLoading(false);

      if (data.done) {
        soundPlayer.stop();
        onInterviewComplete(ticket);
      } else {
        let fullUrl: string | null = null;
        if (data.question_audio_path) {
          const base = await getApiBaseUrl();
          fullUrl = data.question_audio_path.startsWith('http')
            ? data.question_audio_path
            : `${base}${data.question_audio_path}`;
          setAudioSourceUri(fullUrl);
        } else {
          setAudioSourceUri(null);
        }

        if (data.question) {
          playAudio(fullUrl, data.question);
        }
      }
    } catch (err: any) {
      setIsLoading(false);
      Alert.alert('Verification Error', err.message || 'Could not fetch question.');
    }
  };

  useEffect(() => {
    fetchNextQ();
    return () => {
      clearTimers();
      soundPlayer.stop();
    };
  }, []);

  const playAudio = async (targetUri?: string | null, fallbackText?: string) => {
    clearTimers();
    const uriToPlay = targetUri !== undefined ? targetUri : audioSourceUri;
    const textToSpeak = fallbackText || currentQuestion?.question || '';
    const lang = ticket.language || 'hi';

    await soundPlayer.playUrlOrSpeak(uriToPlay, textToSpeak, lang, (playing) => {
      setIsPlayingAudio(playing);
      // When audio question finishes speaking, auto-start microphone (if enabled)
      if (!playing && autoMicRef.current && !isSubmittingRef.current) {
        autoStartTimerRef.current = setTimeout(() => {
          if (!isSubmittingRef.current && !isRecordingRef.current) {
            startVoiceRecording();
          }
        }, 600);
      }
    });
  };

  // Start recording user's voice answer (NO countdown timer)
  const startVoiceRecording = async () => {
    if (isRecordingRef.current || isSubmittingRef.current) return;
    clearTimers();

    try {
      // 1. Stop any currently playing audio
      await soundPlayer.stop();
      setIsPlayingAudio(false);

      // 2. Request mic permission
      const perm = await requestRecordingPermissionsAsync();
      if (!perm.granted) {
        Alert.alert(
          'माइक की अनुमति आवश्यक है (Microphone Needed)',
          'कृपया उत्तर बोलने के लिए माइक्रोफ़ोन की अनुमति दें।'
        );
        return;
      }

      // 3. Switch audio session to recording mode
      await setAudioModeAsync({
        allowsRecording: true,
        playsInSilentMode: true,
      });

      // 4. Give the native audio unit 250ms to settle hardware buffers before starting
      await new Promise((r) => setTimeout(r, 250));

      await audioRecorder.prepareToRecordAsync();
      audioRecorder.record();

      setIsRecording(true);
      isRecordingRef.current = true;
      setRecordedTranscript(null);
      setElapsedSeconds(0);

      // 5. Track elapsed speaking time (counting UP so worker can speak naturally)
      let sec = 0;
      elapsedTimerRef.current = setInterval(() => {
        sec += 1;
        setElapsedSeconds(sec);
      }, 1000);
    } catch (err: any) {
      console.warn('Microphone start error:', err);
      Alert.alert('Microphone Error', err.message || 'Could not activate microphone.');
      setIsRecording(false);
      isRecordingRef.current = false;
      clearTimers();
    }
  };

  // Stop recording, transcribe speech with Whisper, and submit answer
  const stopVoiceRecordingAndSubmit = async () => {
    clearTimers();
    if (!isRecordingRef.current && !isRecording) return;

    try {
      setIsRecording(false);
      isRecordingRef.current = false;
      setIsTranscribing(true);

      await audioRecorder.stop();
      // Allow native audio system 250ms to finish writing m4a headers
      await new Promise((r) => setTimeout(r, 250));

      const uri = audioRecorder.uri;
      if (!uri) {
        setIsTranscribing(false);
        throw new Error('No recorded voice file found.');
      }

      // Validate audio file size
      const info = await FileSystem.getInfoAsync(uri);
      if (info.exists && info.size < 4000) {
        setIsTranscribing(false);
        Alert.alert(
          'आवाज़ बहुत छोटी थी (Recording Too Short)',
          'कृपया माइक बटन दबाकर स्पष्ट रूप से बोलें, फिर "उत्तर भेजें" दबाएं।'
        );
        return;
      }

      // Transcribe via Whisper model on backend
      const res = await transcribeAudioFile(uri, ticket.language);
      const text = res?.transcript?.trim();
      const textEn = res?.transcript_en?.trim();

      if (!text) {
        setIsTranscribing(false);
        Alert.alert(
          'आवाज़ नहीं सुनी गई (No Speech Detected)',
          'स्पष्ट आवाज़ दर्ज नहीं हुई। कृपया फ़ोन के माइक के नज़दीक बोलें या नीचे दिए गए विकल्पों में से चुनें।'
        );
        return;
      }

      setRecordedTranscript(text);
      setIsTranscribing(false);

      // Automatically submit the voice answer
      await handleSelectOption(text, textEn);
    } catch (err: any) {
      setIsTranscribing(false);
      Alert.alert('Voice Error', err.message || 'Failed to process voice response.');
    }
  };

  // Cancel recording without submitting
  const cancelRecording = async () => {
    clearTimers();
    try {
      if (isRecordingRef.current) {
        await audioRecorder.stop();
      }
    } catch {}
    setIsRecording(false);
    isRecordingRef.current = false;
  };

  // Submit answer (from voice, chip click, or text input)
  const handleSelectOption = async (optionText: string, optionTextEn?: string) => {
    if (isSubmittingRef.current || !currentQuestion?.question) return;

    clearTimers();
    if (isRecordingRef.current) {
      try { await audioRecorder.stop(); } catch {}
      setIsRecording(false);
      isRecordingRef.current = false;
    }

    await soundPlayer.stop();
    setIsPlayingAudio(false);

    try {
      setIsSubmitting(true);
      isSubmittingRef.current = true;

      const updatedTicket = await submitVerificationAnswer(
        ticket.id,
        optionText,
        currentQuestion.question,
        optionTextEn
      );

      setIsSubmitting(false);
      isSubmittingRef.current = false;

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
      isSubmittingRef.current = false;
      Alert.alert('Error', err.message || 'Failed to submit answer.');
    }
  };

  // Format elapsed seconds as MM:SS
  const formatTime = (totalSeconds: number) => {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${mins < 10 ? '0' : ''}${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  return (
    <View style={styles.container}>
      <StepIndicator currentStep={3} />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Top Header Row with SOP badge and Auto-mic toggle */}
        <View style={styles.topMetaRow}>
          <View style={styles.sopBadge}>
            <Text style={styles.sopBadgeText}>
              📖 SOP: {currentQuestion?.sop_source || 'BSL Plant Safety Standard'}
            </Text>
          </View>

          <TouchableOpacity
            style={[styles.autoMicPill, autoMicEnabled && styles.autoMicPillActive]}
            onPress={() => setAutoMicEnabled(!autoMicEnabled)}
          >
            <Text style={styles.autoMicPillText}>
              {autoMicEnabled ? '⚡ Auto-Mic: ON' : '⚡ Auto-Mic: OFF'}
            </Text>
          </TouchableOpacity>
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
            {/* Question Card */}
            <View style={styles.questionCard}>
              <Text style={styles.questionText}>{currentQuestion?.question}</Text>
              {audioSourceUri && (
                <TouchableOpacity
                  style={[styles.listenButton, isPlayingAudio && styles.listenButtonPlaying]}
                  onPress={() => playAudio(audioSourceUri)}
                >
                  <Text style={styles.listenButtonText}>
                    {isPlayingAudio ? '🔊 Speaking Question Aloud...' : '🔈 Replay Question Audio'}
                  </Text>
                </TouchableOpacity>
              )}
            </View>

            {/* Voice Input Section (NO COUNTDOWN TIMER) */}
            <View
              style={[
                styles.voiceSection,
                isRecording && styles.voiceSectionActive,
                isPlayingAudio && styles.voiceSectionWaiting,
              ]}
            >
              <View style={styles.voiceHeaderRow}>
                <Text style={styles.voiceSectionTitle}>
                  {isRecording
                    ? `🔴 RECORDING VOICE (${formatTime(elapsedSeconds)})`
                    : isTranscribing
                    ? '⏳ TRANSCRIBING ANSWER...'
                    : isPlayingAudio
                    ? '🔊 LISTENING AFTER QUESTION'
                    : '🎙️ SPEAK YOUR ANSWER (बोलकर उत्तर दें)'}
                </Text>
                {isRecording && (
                  <View style={styles.livePulseBadge}>
                    <Text style={styles.livePulseText}>LIVE</Text>
                  </View>
                )}
              </View>

              {isTranscribing ? (
                <View style={styles.transcribingBox}>
                  <ActivityIndicator size="small" color="#38bdf8" />
                  <Text style={styles.transcribingText}>
                    Transcribing with Whisper Neural AI...
                  </Text>
                </View>
              ) : isRecording ? (
                <View style={styles.recordingActiveContainer}>
                  <Text style={styles.recordingGuideText}>
                    🎙️ बोलें (Speak your answer)...
                  </Text>
                  <Text style={styles.elapsedBadge}>
                    समय: {formatTime(elapsedSeconds)} (बोलने के बाद नीचे टैप करें)
                  </Text>

                  <View style={styles.recordingActionButtons}>
                    <TouchableOpacity
                      style={styles.stopRecordingButton}
                      onPress={stopVoiceRecordingAndSubmit}
                      activeOpacity={0.8}
                    >
                      <Text style={styles.stopRecordingButtonText}>
                        ⏹️ बोलना समाप्त हुआ — उत्तर भेजें (Submit Answer)
                      </Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                      style={styles.cancelRecordingButton}
                      onPress={cancelRecording}
                    >
                      <Text style={styles.cancelRecordingButtonText}>रद्द करें (Cancel)</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              ) : (
                <TouchableOpacity
                  style={[
                    styles.voiceButton,
                    isPlayingAudio && styles.voiceButtonDisabled,
                    isSubmitting && styles.voiceButtonDisabled,
                  ]}
                  onPress={startVoiceRecording}
                  disabled={isSubmitting || isLoading}
                  activeOpacity={0.8}
                >
                  <Text style={styles.voiceIcon}>🎙️</Text>
                  <View style={styles.voiceTextContainer}>
                    <Text style={styles.voiceButtonTitle}>
                      {isPlayingAudio ? 'प्रश्न पढ़ा जा रहा है...' : 'बोलकर उत्तर दें (Tap to Speak)'}
                    </Text>
                    <Text style={styles.voiceButtonSub}>
                      {autoMicEnabled
                        ? 'प्रश्न समाप्त होते ही माइक अपने-आप शुरू होगा'
                        : 'माइक चालू करने के लिए टैप करें (बिना किसी टाइमर के)'}
                    </Text>
                  </View>
                </TouchableOpacity>
              )}

              {recordedTranscript && (
                <View style={styles.transcriptPreview}>
                  <Text style={styles.transcriptLabel}>पहचाना गया (Understood):</Text>
                  <Text style={styles.transcriptContent}>"{recordedTranscript}"</Text>
                </View>
              )}
            </View>

            {/* Divider */}
            <View style={styles.dividerRow}>
              <View style={styles.dividerLine} />
              <Text style={styles.dividerText}>या नीचे दिए गए विकल्प चुनें (OR SELECT OPTION)</Text>
              <View style={styles.dividerLine} />
            </View>

            {/* Answer Options Grid */}
            {currentQuestion?.options.map((opt, idx) => (
              <TouchableOpacity
                key={idx}
                style={styles.optionCard}
                onPress={() => handleSelectOption(opt)}
                disabled={isSubmitting}
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
                placeholder="विवरण टाइप करें (Or type details)..."
                placeholderTextColor="#64748b"
                value={customAnswer}
                onChangeText={setCustomAnswer}
                editable={!isSubmitting}
              />
              <TouchableOpacity
                style={styles.customSendButton}
                disabled={isSubmitting}
                onPress={() => {
                  if (customAnswer.trim()) {
                    handleSelectOption(customAnswer.trim());
                    setCustomAnswer('');
                  }
                }}
              >
                <Text style={styles.customSendText}>भेजें (Send)</Text>
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
    backgroundColor: '#000000',
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 40,
  },
  topMetaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  sopBadge: {
    backgroundColor: '#1c1c1e',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 9999,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
    flex: 1,
    marginRight: 8,
  },
  sopBadgeText: {
    color: '#0A84FF',
    fontSize: 12,
    fontWeight: '600',
  },
  autoMicPill: {
    backgroundColor: '#1c1c1e',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 9999,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
  },
  autoMicPillActive: {
    backgroundColor: 'rgba(48, 209, 88, 0.15)',
    borderColor: 'rgba(48, 209, 88, 0.35)',
  },
  autoMicPillText: {
    color: '#30D158',
    fontSize: 11,
    fontWeight: '600',
  },
  turnLabel: {
    color: 'rgba(235, 235, 245, 0.45)',
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 0.2,
    marginBottom: 12,
  },
  loadingContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 50,
  },
  loadingText: {
    color: '#0A84FF',
    marginTop: 12,
    fontSize: 14,
    fontWeight: '500',
  },
  questionCard: {
    backgroundColor: '#1c1c1e',
    borderRadius: 22,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.15)',
    marginBottom: 18,
  },
  questionText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '700',
    lineHeight: 25,
    marginBottom: 14,
    letterSpacing: -0.3,
  },
  listenButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 9999,
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
  },
  listenButtonPlaying: {
    backgroundColor: 'rgba(10, 132, 255, 0.2)',
    borderColor: '#0A84FF',
  },
  listenButtonText: {
    color: '#0A84FF',
    fontSize: 13,
    fontWeight: '600',
  },
  voiceSection: {
    backgroundColor: '#1c1c1e',
    borderRadius: 20,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
    marginBottom: 18,
  },
  voiceSectionActive: {
    backgroundColor: 'rgba(255, 69, 58, 0.08)',
    borderColor: '#FF453A',
  },
  voiceSectionWaiting: {
    borderColor: '#0A84FF',
  },
  voiceHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  voiceSectionTitle: {
    color: '#0A84FF',
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 0.2,
  },
  livePulseBadge: {
    backgroundColor: '#FF453A',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 9999,
  },
  livePulseText: {
    color: '#ffffff',
    fontSize: 10,
    fontWeight: '700',
  },
  voiceButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(10, 132, 255, 0.1)',
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: '#0A84FF',
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
    color: '#0A84FF',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
    letterSpacing: -0.2,
  },
  voiceButtonSub: {
    color: 'rgba(235, 235, 245, 0.6)',
    fontSize: 12,
  },
  recordingActiveContainer: {
    alignItems: 'center',
    paddingVertical: 8,
  },
  recordingGuideText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 4,
    letterSpacing: -0.2,
  },
  elapsedBadge: {
    color: '#0A84FF',
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 14,
  },
  recordingActionButtons: {
    flexDirection: 'column',
    width: '100%',
  },
  stopRecordingButton: {
    backgroundColor: '#30D158',
    paddingVertical: 14,
    borderRadius: 9999,
    alignItems: 'center',
    marginBottom: 8,
  },
  stopRecordingButtonText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '600',
    letterSpacing: -0.2,
  },
  cancelRecordingButton: {
    paddingVertical: 12,
    backgroundColor: '#2c2c2e',
    borderRadius: 9999,
    alignItems: 'center',
  },
  cancelRecordingButtonText: {
    color: 'rgba(235, 235, 245, 0.65)',
    fontSize: 13,
    fontWeight: '600',
  },
  transcribingBox: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    backgroundColor: '#1c1c1e',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  transcribingText: {
    color: '#0A84FF',
    fontSize: 13,
    fontWeight: '600',
    marginLeft: 10,
  },
  transcriptPreview: {
    marginTop: 12,
    padding: 12,
    backgroundColor: '#000000',
    borderRadius: 14,
    borderLeftWidth: 3,
    borderLeftColor: '#0A84FF',
  },
  transcriptLabel: {
    color: 'rgba(235, 235, 245, 0.45)',
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.2,
  },
  transcriptContent: {
    color: '#ffffff',
    fontSize: 14,
    fontStyle: 'italic',
    marginTop: 4,
  },
  dividerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 14,
  },
  dividerLine: {
    flex: 1,
    height: 0.5,
    backgroundColor: 'rgba(255, 255, 255, 0.12)',
  },
  dividerText: {
    color: 'rgba(235, 235, 245, 0.45)',
    fontSize: 11,
    fontWeight: '600',
    paddingHorizontal: 12,
    letterSpacing: 0.2,
  },
  optionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1c1c1e',
    borderRadius: 18,
    padding: 16,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
  },
  optionIndex: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  optionIndexText: {
    color: '#0A84FF',
    fontSize: 13,
    fontWeight: '700',
  },
  optionText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '500',
    flex: 1,
  },
  customAnswerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 12,
  },
  customInput: {
    flex: 1,
    backgroundColor: '#1c1c1e',
    borderRadius: 9999,
    paddingHorizontal: 16,
    paddingVertical: 12,
    color: '#ffffff',
    fontSize: 14,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.15)',
    marginRight: 8,
  },
  customSendButton: {
    backgroundColor: '#0A84FF',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 9999,
  },
  customSendText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: -0.2,
  },
});
