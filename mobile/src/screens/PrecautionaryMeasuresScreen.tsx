import React, { useState, useEffect } from 'react';
import {
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { createAudioPlayer, setAudioModeAsync } from 'expo-audio';
import { StepIndicator } from '../components/StepIndicator';
import { Ticket } from '../services/api';
import { getApiBaseUrl } from '../services/config';

interface PrecautionaryMeasuresScreenProps {
  ticket: Ticket;
  onProceedToResult: () => void;
}

export const PrecautionaryMeasuresScreen: React.FC<PrecautionaryMeasuresScreenProps> = ({
  ticket,
  onProceedToResult,
}) => {
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  const precautions = ticket.precautionary_measures;
  const measuresList: string[] =
    precautions?.measures_localized ||
    precautions?.measures || [
      'Immediately evacuate upwind of suspected hazard release.',
      'Notify Control Room & establish 360-degree perimeter cordon.',
      'Do not approach unisolated equipment without SCBA / PPE gear.',
    ];

  useEffect(() => {
    const resolveAudio = async () => {
      const path = precautions?.audio_path || ticket.guidance_audio_path;
      if (path) {
        const base = await getApiBaseUrl();
        const fullUrl = path.startsWith('http') ? path : `${base}${path}`;
        setAudioUrl(fullUrl);
      }
    };
    resolveAudio();
  }, [ticket]);

  const [isPlayingAudio, setIsPlayingAudio] = useState<boolean>(false);
  const playerRef = React.useRef<any>(null);

  const playGuidanceAudio = async () => {
    if (!audioUrl) return;
    try {
      setIsPlayingAudio(true);
      await setAudioModeAsync({
        playsInSilentMode: true,
        allowsRecording: false,
      });

      if (playerRef.current) {
        try { playerRef.current.remove(); } catch {}
      }

      const p = createAudioPlayer({ uri: audioUrl });
      playerRef.current = p;
      p.play();

      p.addListener('playbackStatusUpdate', (st: any) => {
        if (st.didJustFinish) {
          setIsPlayingAudio(false);
        }
      });
    } catch {
      setIsPlayingAudio(false);
    }
  };

  return (
    <View style={styles.container}>
      <StepIndicator currentStep={4} />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.alertHeader}>
          <View style={styles.iconCircle}>
            <Text style={styles.iconText}>🛡️</Text>
          </View>
          <View style={styles.headerTitles}>
            <Text style={styles.title}>Personal Safety Precautions</Text>
            <Text style={styles.subtitle}>
              Grounded in BSL Safety Operating Standard SOP
            </Text>
          </View>
        </View>

        {/* Audio Briefing Button */}
        {audioUrl && (
          <TouchableOpacity style={styles.audioBriefingButton} onPress={playGuidanceAudio}>
            <Text style={styles.audioIcon}>🔈</Text>
            <View style={styles.audioTextWrapper}>
              <Text style={styles.audioButtonTitle}>Listen in Your Native Language</Text>
              <Text style={styles.audioButtonSub}>
                Tap to hear verbal safety directives through phone speaker
              </Text>
            </View>
          </TouchableOpacity>
        )}

        {/* Action Directives Checklist */}
        <Text style={styles.sectionHeader}>Mandatory Immediate Actions:</Text>
        {measuresList.map((measure, idx) => (
          <View key={idx} style={styles.measureItem}>
            <View style={styles.bulletNumber}>
              <Text style={styles.bulletText}>{idx + 1}</Text>
            </View>
            <Text style={styles.measureText}>{measure}</Text>
          </View>
        ))}

        {/* Completion Proceed Button */}
        <TouchableOpacity style={styles.proceedButton} onPress={onProceedToResult}>
          <Text style={styles.proceedButtonText}>View Final Safety Ticket & Dossier ➔</Text>
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
  alertHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  iconCircle: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(56, 189, 248, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  iconText: {
    fontSize: 24,
  },
  headerTitles: {
    flex: 1,
  },
  title: {
    color: '#ffffff',
    fontSize: 20,
    fontWeight: '800',
    marginBottom: 2,
  },
  subtitle: {
    color: '#38bdf8',
    fontSize: 12,
    fontWeight: '600',
  },
  audioBriefingButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0f172a',
    borderRadius: 14,
    padding: 16,
    borderWidth: 1.5,
    borderColor: '#38bdf8',
    marginBottom: 22,
  },
  audioIcon: {
    fontSize: 28,
    marginRight: 14,
  },
  audioTextWrapper: {
    flex: 1,
  },
  audioButtonTitle: {
    color: '#38bdf8',
    fontSize: 14,
    fontWeight: '700',
    marginBottom: 2,
  },
  audioButtonSub: {
    color: '#94a3b8',
    fontSize: 11,
  },
  sectionHeader: {
    color: '#cbd5e1',
    fontSize: 13,
    fontWeight: '700',
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  measureItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#0c1626',
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  bulletNumber: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: 'rgba(56, 189, 248, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
    marginTop: 2,
  },
  bulletText: {
    color: '#38bdf8',
    fontSize: 11,
    fontWeight: '800',
  },
  measureText: {
    color: '#ffffff',
    fontSize: 14,
    lineHeight: 20,
    flex: 1,
    fontWeight: '500',
  },
  proceedButton: {
    backgroundColor: '#059669',
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 24,
  },
  proceedButtonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '700',
  },
});
