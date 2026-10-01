import { apiClient } from './client';
import { User, LoginCredentials, RegisterCredentials } from '../types';
import { Platform } from 'react-native';

interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in_minutes: number;
  user_id: string;
  role: string;
}

export const authApi = {
  login: async (
    credentialsOrEmail: LoginCredentials | string,
    optionalPassword?: string
  ): Promise<{ access_token: string; refresh_token: string; user_id: string; email: string; full_name: string; role: string }> => {
    let email = '';
    let password = '';
    if (typeof credentialsOrEmail === 'string') {
      email = credentialsOrEmail;
      password = optionalPassword || '';
    } else {
      email = credentialsOrEmail.email;
      password = credentialsOrEmail.password;
    }

    const response = await apiClient.post<AuthResponse>('/auth/login-json', { email, password });
    const { access_token, refresh_token, user_id, role } = response.data;
    
    return {
      access_token,
      refresh_token,
      user_id,
      email,
      full_name: email.split('@')[0],
      role,
    };
  },

  register: async (
    data: RegisterCredentials
  ): Promise<{ access_token: string; refresh_token: string; user_id: string; email: string; full_name: string }> => {
    await apiClient.post('/auth/register', data);
    return authApi.login(data.email, data.password);
  },

  resetPassword: async (email: string, newPassword: string): Promise<void> => {
    await apiClient.post('/auth/reset-password', {
      email: email.trim().toLowerCase(),
      new_password: newPassword,
    });
  },

  refreshToken: async (refreshToken: string): Promise<string> => {
    const response = await apiClient.post<{ access_token: string }>('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data.access_token;
  },

  logout: async (refreshToken?: string | null): Promise<void> => {
    if (refreshToken) {
      try {
        await apiClient.post('/auth/logout', { refresh_token: refreshToken });
      } catch (e) {
        console.warn('Backend logout notification error:', e);
      }
    }
  },

  getProfile: async (overrideToken?: string): Promise<User> => {
    const headers = overrideToken ? { Authorization: `Bearer ${overrideToken}` } : {};
    const response = await apiClient.get<User>('/auth/me', { headers });
    return response.data;
  },

  updateProfile: async (data: Partial<User>): Promise<User> => {
    const response = await apiClient.put<User>('/auth/me', data);
    return response.data;
  },

  getConsents: async () => {
    const response = await apiClient.get('/auth/me/consents');
    return response.data;
  },

  toggleConsent: async (consentType: string, granted: boolean) => {
    const response = await apiClient.patch(`/auth/me/consents/${consentType}?granted=${granted}`);
    return response.data;
  },

  exportData: async () => {
    const response = await apiClient.get('/auth/me/data-export');
    return response.data;
  },

  deleteAccount: async () => {
    const response = await apiClient.post('/auth/me/delete-account');
    return response.data;
  },

  uploadAvatar: async (fileUri: string): Promise<User> => {
    const formData = new FormData();
    const fileName = `avatar_${Date.now()}.jpg`;
    const mimeType = 'image/jpeg';

    if (Platform.OS === 'web') {
      try {
        const res = await fetch(fileUri);
        const blob = await res.blob();
        formData.append('file', blob, fileName);
      } catch (e) {
        formData.append('file', new Blob(['image data'], { type: mimeType }), fileName);
      }
    } else {
      formData.append('file', {
        uri: fileUri,
        name: fileName,
        type: mimeType,
      } as any);
    }

    const response = await apiClient.post<User>('/auth/avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};
