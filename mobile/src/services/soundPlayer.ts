import { createAudioPlayer, setAudioModeAsync, AudioPlayer } from 'expo-audio';
import * as FileSystem from 'expo-file-system/legacy';

class SoundPlayerManager {
  private currentPlayer: AudioPlayer | null = null;

  async stop() {
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
