import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';
import { User } from '../types';
import { STORAGE_KEYS } from '../constants/config';

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: User | null;
  isLoading: boolean;
  setAuth: (token: string, user: User, refreshToken?: string) => Promise<void>;
  logout: () => Promise<void>;
  loadSession: () => Promise<void>;
  updateUser: (user: User) => void;
}

const isWeb = Platform.OS === 'web';

const storage = {
  setItem: async (key: string, value: string) => {
    if (isWeb) {
      try {
        if (typeof window !== 'undefined' && window.localStorage) {
          window.localStorage.setItem(key, value);
        }
      } catch (e) {
        console.warn('localStorage set error:', e);
      }
    } else {
      try {
        await SecureStore.setItemAsync(key, value);
      } catch (e) {
        console.warn('SecureStore set error:', e);
      }
    }
  },
  getItem: async (key: string) => {
    if (isWeb) {
      try {
        if (typeof window !== 'undefined' && window.localStorage) {
          return window.localStorage.getItem(key);
        }
      } catch (e) {
        console.warn('localStorage get error:', e);
      }
      return null;
    } else {
      try {
        return await SecureStore.getItemAsync(key);
      } catch (e) {
        console.warn('SecureStore get error:', e);
        return null;
      }
    }
  },
  deleteItem: async (key: string) => {
    if (isWeb) {
      try {
        if (typeof window !== 'undefined' && window.localStorage) {
          window.localStorage.removeItem(key);
        }
      } catch (e) {
        console.warn('localStorage delete error:', e);
      }
    } else {
      try {
        await SecureStore.deleteItemAsync(key);
      } catch (e) {
        console.warn('SecureStore delete error:', e);
      }
    }
  },
};

const REFRESH_TOKEN_KEY = 'health_app_refresh_token';

export const useAuthStore = create<AuthState>((set, get) => ({
  token: null,
  refreshToken: null,
  user: null,
  isLoading: true,

  setAuth: async (token: string, user: User, refreshToken?: string) => {
    await storage.setItem(STORAGE_KEYS.AUTH_TOKEN, token);
    await storage.setItem(STORAGE_KEYS.USER_INFO, JSON.stringify(user));
    if (refreshToken) {
      await storage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    }
    set({ token, refreshToken: refreshToken || get().refreshToken, user, isLoading: false });
  },

  logout: async () => {
    await storage.deleteItem(STORAGE_KEYS.AUTH_TOKEN);
    await storage.deleteItem(STORAGE_KEYS.USER_INFO);
    await storage.deleteItem(REFRESH_TOKEN_KEY);
    set({ token: null, refreshToken: null, user: null, isLoading: false });
  },

  loadSession: async () => {
    try {
      const token = await storage.getItem(STORAGE_KEYS.AUTH_TOKEN);
      const refreshToken = await storage.getItem(REFRESH_TOKEN_KEY);
      const userStr = await storage.getItem(STORAGE_KEYS.USER_INFO);
      if (token && userStr) {
        const user = JSON.parse(userStr);
        if (!user.role && (user.email?.startsWith('admin@') || user.full_name?.toLowerCase().includes('administrator'))) {
          user.role = 'ADMIN';
        }
        set({ token, refreshToken, user, isLoading: false });
        return;
      }
    } catch (e) {
      console.warn('Load session error:', e);
    }
    set({ token: null, refreshToken: null, user: null, isLoading: false });
  },

  updateUser: (user: User) => {
    storage.setItem(STORAGE_KEYS.USER_INFO, JSON.stringify(user));
    set({ user });
  },
}));
