import { createAudioPlayer, setAudioModeAsync, AudioPlayer } from 'expo-audio';
import * as FileSystem from 'expo-file-system/legacy';
import * as Speech from 'expo-speech';

class SoundPlayerManager {
  private currentPlayer: AudioPlayer | null = null;
  private isSpeakingOffline: boolean = false;

  async stop() {
    try {
      Speech.stop();
      this.isSpeakingOffline = false;
    } catch (e) {}

    if (this.currentPlayer) {
      try {
        this.currentPlayer.pause();
        this.currentPlayer.remove();
      } catch (err) {
        console.warn('Error stopping audio player:', err);
      }
      this.currentPlayer = null;
    }
  }

  async speakOffline(
    text: string,
    language: string = 'hi',
    onStatusUpdate?: (isPlaying: boolean) => void
  ) {
    await this.stop();
    if (!text || !text.trim()) {
      if (onStatusUpdate) onStatusUpdate(false);
      return;
    }

    const langMap: Record<string, string> = {
      hi: 'hi-IN',
      en: 'en-IN',
      bn: 'bn-IN',
      ta: 'ta-IN',
      te: 'te-IN',
      mr: 'mr-IN',
      gu: 'gu-IN',
      kn: 'kn-IN',
      ml: 'ml-IN',
      pa: 'pa-IN',
      or: 'hi-IN',
    };
    const voiceLang = langMap[(language || 'hi').toLowerCase()] || 'hi-IN';

    this.isSpeakingOffline = true;
    if (onStatusUpdate) onStatusUpdate(true);

    try {
      Speech.speak(text.trim(), {
        language: voiceLang,
        pitch: 1.0,
        rate: 0.95,
        onDone: () => {
          this.isSpeakingOffline = false;
          if (onStatusUpdate) onStatusUpdate(false);
        },
        onStopped: () => {
          this.isSpeakingOffline = false;
          if (onStatusUpdate) onStatusUpdate(false);
        },
        onError: (err) => {
          console.warn('[SoundPlayer] On-device offline TTS error:', err);
          this.isSpeakingOffline = false;
          if (onStatusUpdate) onStatusUpdate(false);
        },
      });
    } catch (err) {
      console.warn('[SoundPlayer] Speech.speak call failed:', err);
      this.isSpeakingOffline = false;
      if (onStatusUpdate) onStatusUpdate(false);
    }
  }

  async playUrlOrSpeak(
    url: string | null | undefined,
    fallbackText: string,
    language: string = 'hi',
    onStatusUpdate?: (isPlaying: boolean) => void
  ): Promise<boolean> {
    if (url) {
      const res = await this.playUrl(url, onStatusUpdate);
      if (res) return true;
    }

    // If server audio URL is missing or failed to stream/download, fall back to offline speech synthesis
    console.log('[SoundPlayer] Falling back to on-device speech synthesis for text length:', fallbackText.length);
    await this.speakOffline(fallbackText, language, onStatusUpdate);
    return true;
  }

  async playUrl(
    remoteOrLocalUrl: string,
    onStatusUpdate?: (isPlaying: boolean) => void
  ): Promise<AudioPlayer | null> {
    try {
      await this.stop();

      // Configure audio session for loud speaker playback on iOS & Android
      await setAudioModeAsync({
        playsInSilentMode: true,
        allowsRecording: false,
        shouldRouteThroughEarpiece: false,
        shouldPlayInBackground: false,
      });

      let playUri = remoteOrLocalUrl;

      // If remote HTTP/HTTPS, download to local cache directory for instant lag-free native playback
      if (remoteOrLocalUrl.startsWith('http://') || remoteOrLocalUrl.startsWith('https://')) {
        const rawName = remoteOrLocalUrl.split('?')[0].split('/').pop() || `audio_${Date.now()}.mp3`;
        const localTarget = `${FileSystem.cacheDirectory}${rawName}`;

        try {
          const fileInfo = await FileSystem.getInfoAsync(localTarget);
          if (fileInfo.exists) {
            playUri = localTarget;
          } else {
            console.log('[SoundPlayer] Pre-downloading audio to cache:', remoteOrLocalUrl);
            const downloadRes = await FileSystem.downloadAsync(remoteOrLocalUrl, localTarget);
            playUri = downloadRes.uri;
          }
        } catch (downloadErr) {
          console.warn('[SoundPlayer] Cache download failed, falling back to direct URL:', downloadErr);
          playUri = remoteOrLocalUrl;
        }
      }

      console.log('[SoundPlayer] Starting native audio playback from:', playUri);

      // Create player directly with the resolved local file URI
      const player = createAudioPlayer(playUri);
      player.volume = 1.0;
      this.currentPlayer = player;

      if (onStatusUpdate) onStatusUpdate(true);

      player.addListener('playbackStatusUpdate', (status: any) => {
        if (status.didJustFinish) {
          if (onStatusUpdate) onStatusUpdate(false);
        }
      });

      player.play();
      return player;
    } catch (err: any) {
      console.warn('[SoundPlayer] Playback error:', err);
      if (onStatusUpdate) onStatusUpdate(false);
      return null;
    }
  }
}

export const soundPlayer = new SoundPlayerManager();
