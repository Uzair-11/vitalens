import { Platform } from 'react-native';
import Constants from 'expo-constants';

// ─── IP CONFIGURATION ─────────────────────────────────────────────────────────
// Automatically detect the dev machine IP from Expo's hostUri, with fallback
// to active Wi-Fi LAN IP (192.168.1.3).
// ──────────────────────────────────────────────────────────────────────────────
const DEFAULT_DEV_IP = '192.168.1.3';

const getDevMachineIP = (): string => {
  try {
    const candidateUri =
      Constants.expoConfig?.hostUri ||
      (Constants as any).expoGoConfig?.debuggerHost ||
      (Constants as any).manifest2?.extra?.expoGo?.debuggerHost ||
      (Constants as any).manifest2?.extra?.expoClient?.hostUri ||
      (Constants as any).manifest?.debuggerHost ||
      (Constants as any).manifest?.bundleUrl ||
      (Constants as any).experienceUrl ||
      (Constants as any).linkingUri;

    if (candidateUri && typeof candidateUri === 'string') {
      const cleanUri = candidateUri.replace(/^https?:\/\//, '').replace(/^exp:\/\//, '');
      const ip = cleanUri.split(':')[0].split('/')[0];
      if (ip && ip !== 'localhost' && ip !== '127.0.0.1') {
        return ip;
      }
    }
  } catch (e) {
    console.warn('[VitaLens Config] Could not auto-detect dev host IP:', e);
  }
  return DEFAULT_DEV_IP;
};

export const DEV_MACHINE_IP = getDevMachineIP();

const getBaseUrl = () => {
  if (Platform.OS === 'web') {
    return 'http://localhost:8000/api/v1';
  }
  // Android / iOS physical device or emulator connecting to dev machine backend
  return `http://${DEV_MACHINE_IP}:8000/api/v1`;
};

export const API_CONFIG = {
  BASE_URL: getBaseUrl(),
  FALLBACK_URL: `http://${DEV_MACHINE_IP}:8000/api/v1`,
  TIMEOUT_MS: 20000,
};

console.log(`[VitaLens Network Config] Platform: ${Platform.OS} | Host IP: ${DEV_MACHINE_IP} | Base URL: ${API_CONFIG.BASE_URL}`);

export const STORAGE_KEYS = {
  AUTH_TOKEN: 'health_app_auth_token',
  USER_INFO: 'health_app_user_info',
};

export const getMediaUrl = (pathOrUrl?: string | null): string | null => {
  if (!pathOrUrl) return null;
  if (pathOrUrl.startsWith('http://') || pathOrUrl.startsWith('https://')) {
    return pathOrUrl;
  }
  const base = Platform.OS === 'web' ? 'http://localhost:8000' : `http://${DEV_MACHINE_IP}:8000`;
  return `${base}${pathOrUrl.startsWith('/') ? '' : '/'}${pathOrUrl}`;
};
