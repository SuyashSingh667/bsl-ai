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
        <View style={[styles.headerBadge, { borderColor: 'rgba(255, 255, 255, 0.15)', backgroundColor: '#1c1c1e' }]}>
          <Text style={[styles.headerBadgeText, { color: 'rgba(235, 235, 245, 0.85)' }]}>📸 FIELD EVIDENCE (OPTIONAL)</Text>
        </View>

        <Text style={styles.title}>Physical Evidence Attachment</Text>
        <Text style={styles.subtitle}>
          Uploading a photograph or video is <Text style={[styles.highlightText, { color: '#ffffff' }]}>OPTIONAL</Text>.
          Visual proof helps AI and emergency crews locate hazards faster, but is never required to submit a report.
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

        {/* Skip Button: Evidence upload is optional */}
        <View style={styles.skipContainer}>
          <TouchableOpacity style={styles.skipButton} onPress={onSkip}>
            <Text style={styles.skipButtonText}>
              Skip & Continue to Verification ➔
            </Text>
          </TouchableOpacity>
          <Text style={styles.skipNotice}>
            Photo/video proof is optional and never required. You can proceed directly to report verification at any time.
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
  headerBadge: {
    backgroundColor: '#1c1c1e',
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 9999,
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderColor: 'rgba(255, 69, 58, 0.4)',
    marginBottom: 12,
  },
  headerBadgeText: {
    color: '#FF453A',
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.2,
  },
  title: {
    color: '#ffffff',
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 6,
    letterSpacing: -0.5,
  },
  subtitle: {
    color: 'rgba(235, 235, 245, 0.65)',
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 20,
  },
  highlightText: {
    color: '#ffffff',
    fontWeight: '600',
  },
  optionsContainer: {
    marginBottom: 20,
  },
  actionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1c1c1e',
    borderRadius: 20,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
  },
  iconCircleBlue: {
    width: 44,
    height: 44,
    borderRadius: 14,
    backgroundColor: '#2c2c2e',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  iconCircleRed: {
    width: 44,
    height: 44,
    borderRadius: 14,
    backgroundColor: '#2c2c2e',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  iconCircleGreen: {
    width: 44,
    height: 44,
    borderRadius: 14,
    backgroundColor: '#2c2c2e',
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
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
    letterSpacing: -0.2,
  },
  actionSub: {
    color: 'rgba(235, 235, 245, 0.45)',
    fontSize: 12,
  },
  previewCard: {
    backgroundColor: '#1c1c1e',
    borderRadius: 22,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.15)',
    marginBottom: 20,
  },
  previewImage: {
    width: '100%',
    height: 240,
  },
  videoPlaceholder: {
    width: '100%',
    height: 200,
    backgroundColor: '#1c1c1e',
    justifyContent: 'center',
    alignItems: 'center',
  },
  videoPlaceholderIcon: {
    fontSize: 48,
    marginBottom: 8,
  },
  videoPlaceholderText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
  previewActions: {
    flexDirection: 'row',
    padding: 14,
    justifyContent: 'space-between',
  },
  retakeButton: {
    paddingVertical: 12,
    paddingHorizontal: 18,
    borderRadius: 9999,
    backgroundColor: '#2c2c2e',
  },
  retakeButtonText: {
    color: 'rgba(235, 235, 245, 0.65)',
    fontSize: 14,
    fontWeight: '600',
  },
  uploadConfirmButton: {
    backgroundColor: '#ffffff',
    paddingVertical: 12,
    paddingHorizontal: 22,
    borderRadius: 9999,
  },
  uploadConfirmText: {
    color: '#000000',
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: -0.2,
  },
  skipContainer: {
    marginTop: 10,
    alignItems: 'center',
  },
  skipButton: {
    backgroundColor: '#1c1c1e',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 9999,
    width: '100%',
    alignItems: 'center',
    marginBottom: 8,
  },
  skipButtonText: {
    color: 'rgba(235, 235, 245, 0.65)',
    fontSize: 14,
    fontWeight: '600',
  },
  skipNotice: {
    color: 'rgba(235, 235, 245, 0.45)',
    fontSize: 11,
    textAlign: 'center',
    paddingHorizontal: 10,
  },
});
