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
import { useAudioPlayer } from 'expo-audio';
import { StepIndicator } from '../components/StepIndicator';
import {
  getNextQuestion,
  NextQuestionResponse,
  submitVerificationAnswer,
  Ticket,
} from '../services/api';
import { getApiBaseUrl } from '../services/config';

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

  // Modern SDK 57 audio player hook
  const player = useAudioPlayer(audioSourceUri ? { uri: audioSourceUri } : null);

  // Fetch next question from adaptive verification engine
  const fetchNextQ = async () => {
    try {
      setIsLoading(true);
      const data = await getNextQuestion(ticket.id, ticket.language);
      setCurrentQuestion(data);
      setIsLoading(false);

      if (data.done) {
        onInterviewComplete(ticket);
      } else if (data.question_audio_path) {
        const base = await getApiBaseUrl();
        const fullUrl = data.question_audio_path.startsWith('http')
          ? data.question_audio_path
          : `${base}${data.question_audio_path}`;
        setAudioSourceUri(fullUrl);
      }
    } catch (err: any) {
      setIsLoading(false);
      Alert.alert('Verification Error', err.message || 'Could not fetch question.');
    }
  };

  useEffect(() => {
    fetchNextQ();
  }, []);

  const playAudio = () => {
    try {
      if (player) {
        player.seekTo(0);
        player.play();
      }
    } catch {
      // ignore
    }
  };

  // Submit selected option chip
  const handleSelectOption = async (optionText: string) => {
    if (isSubmitting || !currentQuestion?.question) return;
    try {
      setIsSubmitting(true);
      const updatedTicket = await submitVerificationAnswer(
        ticket.id,
        optionText,
        currentQuestion.question
      );
      setIsSubmitting(false);

      // Check if all turns are done
      if (
        (currentQuestion.question_index ?? 0) + 1 >= currentQuestion.total_questions ||
        updatedTicket.verification_status !== 'pending'
      ) {
        onInterviewComplete(updatedTicket);
      } else {
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
                <TouchableOpacity style={styles.listenButton} onPress={playAudio}>
                  <Text style={styles.listenButtonText}>🔈 Listen to Question</Text>
                </TouchableOpacity>
              )}
            </View>

            {/* Answer Options Grid */}
            <Text style={styles.optionsPrompt}>Select the matching field condition:</Text>
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
                placeholder="Or type specific detail..."
                placeholderTextColor="#64748b"
                value={customAnswer}
                onChangeText={setCustomAnswer}
              />
              <TouchableOpacity
                style={styles.customSendButton}
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
    marginBottom: 20,
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
  },
  listenButtonText: {
    color: '#38bdf8',
    fontSize: 12,
    fontWeight: '600',
  },
  optionsPrompt: {
    color: '#cbd5e1',
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 10,
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
    marginTop: 14,
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
