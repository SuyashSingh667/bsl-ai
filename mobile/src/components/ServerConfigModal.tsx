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
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalCard: {
    width: '100%',
    backgroundColor: '#0f172a',
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  title: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 8,
  },
  description: {
    color: '#94a3b8',
    fontSize: 13,
    lineHeight: 18,
    marginBottom: 16,
  },
  input: {
    backgroundColor: '#070d18',
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    color: '#38bdf8',
    fontSize: 14,
    borderWidth: 1,
    borderColor: '#334155',
    marginBottom: 20,
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 12,
  },
  cancelButton: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: '#1e293b',
  },
  cancelText: {
    color: '#94a3b8',
    fontSize: 13,
    fontWeight: '600',
  },
  saveButton: {
    backgroundColor: '#2563eb',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  saveText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '700',
  },
});
