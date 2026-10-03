import { apiClient } from './client';
import { User, LoginCredentials, RegisterCredentials } from '../types';
import { Platform } from 'react-native';
import { API_CONFIG } from '../constants/config';
import { useAuthStore } from '../store/authStore';
import { getFileBlob } from './reportApi';

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

  resetPassword: async (email: string, newPassword: string, otp?: string): Promise<void> => {
    if (otp) {
      await apiClient.post('/auth/forgot-password/reset', {
        email: email.trim().toLowerCase(),
        otp: otp.trim(),
        new_password: newPassword,
      });
    } else {
      await apiClient.post('/auth/reset-password', {
        email: email.trim().toLowerCase(),
        new_password: newPassword,
      });
    }
  },

  sendVerificationOtp: async (email: string): Promise<{ status: string; message: string; dev_otp?: string }> => {
    const response = await apiClient.post('/auth/send-verification-otp', { email: email.trim().toLowerCase() });
    return response.data;
  },

  verifyEmailOtp: async (email: string, otp: string): Promise<{ status: string; message: string; email_verified: boolean; is_verified: boolean }> => {
    const response = await apiClient.post('/auth/verify-email-otp', {
      email: email.trim().toLowerCase(),
      otp: otp.trim(),
    });
    return response.data;
  },

  forgotPasswordRequestOtp: async (email: string): Promise<{ status: string; message: string; dev_otp?: string }> => {
    const response = await apiClient.post('/auth/forgot-password/request-otp', {
      email: email.trim().toLowerCase(),
    });
    return response.data;
  },

  forgotPasswordVerifyOtp: async (email: string, otp: string): Promise<{ status: string; message: string }> => {
    const response = await apiClient.post('/auth/forgot-password/verify-otp', {
      email: email.trim().toLowerCase(),
      otp: otp.trim(),
    });
    return response.data;
  },

  forgotPasswordReset: async (email: string, otp: string, newPassword: string): Promise<{ status: string; message: string }> => {
    const response = await apiClient.post('/auth/forgot-password/reset', {
      email: email.trim().toLowerCase(),
      otp: otp.trim(),
      new_password: newPassword,
    });
    return response.data;
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

  linkAbha: async (abhaNumber: string): Promise<{ status: string; message: string; abha_number: string }> => {
    const response = await apiClient.post('/me/abha/link', { abha_number: abhaNumber });
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
    const fileName = `avatar_${Date.now()}.jpg`;
    const mimeType = 'image/jpeg';
    const token = useAuthStore.getState().token;
    const url = `${API_CONFIG.BASE_URL}/auth/avatar`;

    const blob = await getFileBlob(fileUri, mimeType);
    const formData = new FormData();
    formData.append('file', blob, fileName);

    const headers: Record<string, string> = { Accept: 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    try {
      const res = await fetch(url, { method: 'POST', headers, body: formData });
      const resData = await res.json().catch(() => null);
      if (!res.ok) {
        const errorDetail = resData?.detail || `Upload failed with status ${res.status}`;
        throw new Error(typeof errorDetail === 'string' ? errorDetail : JSON.stringify(errorDetail));
      }
      return resData;
    } catch (fetchErr: any) {
      if (fetchErr.message && !fetchErr.message.includes('Network request failed')) {
        throw fetchErr;
      }
      // Fallback: XHR
      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', url);
        xhr.setRequestHeader('Accept', 'application/json');
        if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`);
        xhr.onload = () => {
          let data: any = null;
          try { data = JSON.parse(xhr.responseText); } catch { data = xhr.responseText; }
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(data);
          } else {
            const errorDetail = data?.detail || `Upload failed with status ${xhr.status}`;
            reject(new Error(typeof errorDetail === 'string' ? errorDetail : JSON.stringify(errorDetail)));
          }
        };
        xhr.onerror = (e) => reject(new Error('Network Error: Failed to upload avatar.'));
        xhr.send(formData);
      });
    }
  },
};
