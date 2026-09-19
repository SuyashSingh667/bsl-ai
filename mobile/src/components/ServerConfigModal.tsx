import React, { useEffect, useState } from 'react';
import {
  Alert,
  Modal,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { DEFAULT_API_BASE_URL, getApiBaseUrl, setApiBaseUrl } from '../services/config';

interface ServerConfigModalProps {
  visible: boolean;
  onClose: () => void;
}

export const ServerConfigModal: React.FC<ServerConfigModalProps> = ({ visible, onClose }) => {
  const [currentUrl, setCurrentUrl] = useState<string>(DEFAULT_API_BASE_URL);

  useEffect(() => {
    if (visible) {
      getApiBaseUrl().then((url) => setCurrentUrl(url));
    }
  }, [visible]);

  const handleSave = async () => {
    if (!currentUrl.trim()) {
      Alert.alert('Invalid URL', 'Please enter a valid server URL');
      return;
    }
    await setApiBaseUrl(currentUrl.trim());
    Alert.alert('Saved', 'Plant server IP updated successfully.');
    onClose();
  };

  return (
    <Modal visible={visible} animationType="slide" transparent>
      <View style={styles.overlay}>
        <View style={styles.modalCard}>
          <Text style={styles.title}>⚙️ Plant Server Settings</Text>
          <Text style={styles.description}>
            Enter the local IP address and port of your computer or plant server where FastAPI is running:
          </Text>

          <TextInput
            style={styles.input}
            value={currentUrl}
            onChangeText={setCurrentUrl}
            placeholder="http://192.168.1.100:8000"
            placeholderTextColor="#64748b"
            autoCapitalize="none"
            autoCorrect={false}
          />

          <View style={styles.buttonRow}>
            <TouchableOpacity style={styles.cancelButton} onPress={onClose}>
              <Text style={styles.cancelText}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.saveButton} onPress={handleSave}>
              <Text style={styles.saveText}>Save IP</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.85)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalCard: {
    width: '100%',
    backgroundColor: '#1c1c1e',
    borderRadius: 24,
    padding: 22,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.15)',
  },
  title: {
    color: '#ffffff',
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 8,
    letterSpacing: -0.3,
  },
  description: {
    color: 'rgba(235, 235, 245, 0.65)',
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 16,
  },
  input: {
    backgroundColor: '#000000',
    borderRadius: 14,
    paddingHorizontal: 16,
    paddingVertical: 14,
    color: '#0A84FF',
    fontSize: 15,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.15)',
    marginBottom: 20,
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 12,
  },
  cancelButton: {
    paddingVertical: 12,
    paddingHorizontal: 18,
    borderRadius: 9999,
    backgroundColor: '#2c2c2e',
  },
  cancelText: {
    color: 'rgba(235, 235, 245, 0.65)',
    fontSize: 14,
    fontWeight: '600',
  },
  saveButton: {
    backgroundColor: '#0A84FF',
    paddingVertical: 12,
    paddingHorizontal: 22,
    borderRadius: 9999,
  },
  saveText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: -0.2,
  },
});
