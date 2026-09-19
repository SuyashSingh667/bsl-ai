import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';

// Fallback LAN IP
export const DEFAULT_API_BASE_URL = 'http://10.12.3.58:8000';

const STORAGE_KEY = '@bsl_api_base_url';

export async function getApiBaseUrl(): Promise<string> {
  try {
    const custom = await AsyncStorage.getItem(STORAGE_KEY);
    if (custom && custom.trim().length > 0) {
      return custom.trim().replace(/\/+$/, '');
    }

    // Automatically extract host IP from Expo bundler connection (Expo Go on phone)
    const hostUri = Constants.expoConfig?.hostUri || (Constants as any).manifest2?.extra?.expoGo?.debuggerHost || (Constants as any).manifest?.debuggerHost;
    if (hostUri) {
      const ip = hostUri.split(':')[0];
      if (ip && ip !== 'localhost' && ip !== '127.0.0.1') {
        return `http://${ip}:8000`;
      }
    }
  } catch {
    // fallback
  }
  return DEFAULT_API_BASE_URL;
}

export async function setApiBaseUrl(url: string): Promise<void> {
  try {
    await AsyncStorage.setItem(STORAGE_KEY, url.trim().replace(/\/+$/, ''));
  } catch (err) {
    console.error('Failed to save API base URL', err);
  }
}

export const INTAKE_LANGUAGES = [
  { code: 'hi', label: 'हिन्दी' },
  { code: 'bn', label: 'বাংলা' },
  { code: 'ta', label: 'தமிழ்' },
  { code: 'te', label: 'తెలుగు' },
  { code: 'mr', label: 'मराठी' },
  { code: 'gu', label: 'ગુજરાતી' },
  { code: 'kn', label: 'ಕನ್ನಡ' },
  { code: 'ml', label: 'മലയാളം' },
  { code: 'pa', label: 'ਪੰਜਾਬੀ' },
  { code: 'or', label: 'ଓଡ଼ିଆ' },
  { code: 'en', label: 'English' },
];
