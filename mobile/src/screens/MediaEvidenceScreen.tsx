import React, { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Image,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { StepIndicator } from '../components/StepIndicator';
import { Ticket, uploadTicketMedia } from '../services/api';

interface MediaEvidenceScreenProps {
  ticket: Ticket;
  onMediaUploaded: (updatedTicket: Ticket) => void;
  onSkip: () => void;
}

export const MediaEvidenceScreen: React.FC<MediaEvidenceScreenProps> = ({
  ticket,
  onMediaUploaded,
  onSkip,
}) => {
  const [mediaUri, setMediaUri] = useState<string | null>(null);
  const [mediaType, setMediaType] = useState<'image' | 'video'>('image');
  const [isUploading, setIsUploading] = useState<boolean>(false);

  // Take photo directly with native camera
  const takePhotoWithCamera = async () => {
    try {
      const perm = await ImagePicker.requestCameraPermissionsAsync();
      if (perm.status !== 'granted') {
        Alert.alert('Camera Access', 'Please allow camera access to take incident proof photographs.');
        return;
      }
      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        quality: 0.8,
      });

      if (!result.canceled && result.assets && result.assets[0]) {
        setMediaUri(result.assets[0].uri);
        setMediaType('image');
      }
    } catch (err: any) {
      Alert.alert('Camera Error', err.message || 'Could not open camera.');
    }
  };

  // Record short video with camera
  const recordVideoWithCamera = async () => {
    try {
      const perm = await ImagePicker.requestCameraPermissionsAsync();
      if (perm.status !== 'granted') {
        Alert.alert('Camera Access', 'Please allow camera access to record video proof.');
        return;
      }
      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Videos,
        videoMaxDuration: 30,
        quality: 0.7,
      });

      if (!result.canceled && result.assets && result.assets[0]) {
        setMediaUri(result.assets[0].uri);
        setMediaType('video');
      }
    } catch (err: any) {
      Alert.alert('Video Error', err.message || 'Could not open camera.');
    }
  };

  // Pick from device photo gallery
  const pickFromGallery = async () => {
    try {
      const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (perm.status !== 'granted') {
        Alert.alert('Gallery Access', 'Please allow gallery access to select media.');
        return;
      }
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.All,
        quality: 0.8,
      });

      if (!result.canceled && result.assets && result.assets[0]) {
        const asset = result.assets[0];
        setMediaUri(asset.uri);
        setMediaType(asset.type === 'video' ? 'video' : 'image');
      }
    } catch (err: any) {
      Alert.alert('Gallery Error', err.message || 'Could not open gallery.');
    }
  };

  // Submit media to backend
  const uploadProof = async () => {
    if (!mediaUri) return;
    try {
      setIsUploading(true);
      const updated = await uploadTicketMedia(ticket.id, mediaUri, mediaType);
      setIsUploading(false);
      onMediaUploaded(updated);
    } catch (err: any) {
      setIsUploading(false);
      Alert.alert('Upload Failed', err.message || 'Failed to attach media proof.');
    }
  };

  return (
    <View style={styles.container}>
      <StepIndicator currentStep={2} />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.headerBadge}>
          <Text style={styles.headerBadgeText}>📸 MANDATORY EVIDENCE PROTOCOL</Text>
        </View>

        <Text style={styles.title}>Physical Evidence Capture</Text>
        <Text style={styles.subtitle}>
          BSL Safety Protocol requires a clear photograph or video for{' '}
          <Text style={styles.highlightText}>
            {ticket.predicted_category?.replace('_', ' ').toUpperCase() || 'THIS INCIDENT'}
          </Text>{' '}
          to verify hazard boundaries before dispatching crews.
        </Text>

        {/* Media Preview or Capture Options */}
        {mediaUri ? (
          <View style={styles.previewCard}>
            {mediaType === 'image' ? (
              <Image source={{ uri: mediaUri }} style={styles.previewImage} resizeMode="cover" />
            ) : (
              <View style={styles.videoPlaceholder}>
                <Text style={styles.videoPlaceholderIcon}>🎥</Text>
                <Text style={styles.videoPlaceholderText}>Video Proof Captured</Text>
              </View>
            )}

            <View style={styles.previewActions}>
              <TouchableOpacity
                style={styles.retakeButton}
                onPress={() => setMediaUri(null)}
                disabled={isUploading}
              >
                <Text style={styles.retakeButtonText}>🔄 Retake Media</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.uploadConfirmButton}
                onPress={uploadProof}
                disabled={isUploading}
              >
                {isUploading ? (
                  <ActivityIndicator size="small" color="#ffffff" />
                ) : (
                  <Text style={styles.uploadConfirmText}>Attach Evidence ➔</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        ) : (
          <View style={styles.optionsContainer}>
            {/* Camera Photo */}
            <TouchableOpacity style={styles.actionCard} onPress={takePhotoWithCamera}>
              <View style={styles.iconCircleBlue}>
                <Text style={styles.actionIcon}>📸</Text>
              </View>
              <View style={styles.actionDetails}>
                <Text style={styles.actionTitle}>Take Photograph</Text>
                <Text style={styles.actionSub}>Open native phone camera to snap evidence</Text>
              </View>
            </TouchableOpacity>

            {/* Camera Video */}
            <TouchableOpacity style={styles.actionCard} onPress={recordVideoWithCamera}>
              <View style={styles.iconCircleRed}>
                <Text style={styles.actionIcon}>📹</Text>
              </View>
              <View style={styles.actionDetails}>
                <Text style={styles.actionTitle}>Record Short Video</Text>
                <Text style={styles.actionSub}>Capture 15-30s video of flame, leak, or spill</Text>
              </View>
            </TouchableOpacity>

            {/* Device Gallery */}
            <TouchableOpacity style={styles.actionCard} onPress={pickFromGallery}>
              <View style={styles.iconCircleGreen}>
                <Text style={styles.actionIcon}>🖼️</Text>
              </View>
              <View style={styles.actionDetails}>
                <Text style={styles.actionTitle}>Choose from Gallery</Text>
                <Text style={styles.actionSub}>Select existing photo or video from device</Text>
              </View>
            </TouchableOpacity>
          </View>
        )}

        {/* Skip Button for Dangerous Situations */}
        <View style={styles.skipContainer}>
          <TouchableOpacity style={styles.skipButton} onPress={onSkip}>
            <Text style={styles.skipButtonText}>
              ⚠️ Unsafe to Photograph? Skip to Verification ➔
            </Text>
          </TouchableOpacity>
          <Text style={styles.skipNotice}>
            Only skip if taking a photograph puts you or other workers in immediate physical danger.
          </Text>
        </View>
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
  headerBadge: {
    backgroundColor: 'rgba(239, 68, 68, 0.15)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderColor: 'rgba(239, 68, 68, 0.3)',
    marginBottom: 10,
  },
  headerBadgeText: {
    color: '#f87171',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  title: {
    color: '#ffffff',
    fontSize: 22,
    fontWeight: '800',
    marginBottom: 6,
  },
  subtitle: {
    color: '#94a3b8',
    fontSize: 13,
    lineHeight: 18,
    marginBottom: 20,
  },
  highlightText: {
    color: '#38bdf8',
    fontWeight: '700',
  },
  optionsContainer: {
    marginBottom: 20,
  },
  actionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0f172a',
    borderRadius: 14,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  iconCircleBlue: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(37, 99, 235, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  iconCircleRed: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  iconCircleGreen: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(16, 185, 129, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  actionIcon: {
    fontSize: 22,
  },
  actionDetails: {
    flex: 1,
  },
  actionTitle: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '700',
    marginBottom: 2,
  },
  actionSub: {
    color: '#64748b',
    fontSize: 12,
  },
  previewCard: {
    backgroundColor: '#0f172a',
    borderRadius: 14,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#1e293b',
    marginBottom: 20,
  },
  previewImage: {
    width: '100%',
    height: 240,
  },
  videoPlaceholder: {
    width: '100%',
    height: 200,
    backgroundColor: '#1e293b',
    justifyContent: 'center',
    alignItems: 'center',
  },
  videoPlaceholderIcon: {
    fontSize: 48,
    marginBottom: 8,
  },
  videoPlaceholderText: {
    color: '#38bdf8',
    fontSize: 14,
    fontWeight: '700',
  },
  previewActions: {
    flexDirection: 'row',
    padding: 12,
    justifyContent: 'space-between',
  },
  retakeButton: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: '#1e293b',
  },
  retakeButtonText: {
    color: '#94a3b8',
    fontSize: 13,
    fontWeight: '600',
  },
  uploadConfirmButton: {
    backgroundColor: '#2563eb',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  uploadConfirmText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '700',
  },
  skipContainer: {
    marginTop: 10,
    alignItems: 'center',
  },
  skipButton: {
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(239, 68, 68, 0.4)',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 10,
    width: '100%',
    alignItems: 'center',
    marginBottom: 6,
  },
  skipButtonText: {
    color: '#f87171',
    fontSize: 12,
    fontWeight: '700',
  },
  skipNotice: {
    color: '#64748b',
    fontSize: 11,
    textAlign: 'center',
    paddingHorizontal: 10,
  },
});
