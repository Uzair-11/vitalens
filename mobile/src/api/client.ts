import axios from 'axios';
import { API_CONFIG } from '../constants/config';
import { useAuthStore } from '../store/authStore';

export const apiClient = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  timeout: API_CONFIG.TIMEOUT_MS,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token, handle FormData headers, and log requests
apiClient.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // If uploading FormData (e.g. multipart report files), remove the default application/json
    // so React Native's XMLHttpRequest automatically appends the multipart boundary header
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type'];
    }

    const fullUrl = `${config.baseURL || ''}${config.url || ''}`;
    console.log(`📡 [API REQ] ${config.method?.toUpperCase()} ${fullUrl}`);

    return config;
  },
  (error) => {
    console.error('❌ [API REQ ERROR]', error);
    return Promise.reject(error);
  }
);

// Response interceptor for automatic token refresh on 401 & structured diagnostic logging
let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => {
    console.log(`✅ [API RES] ${response.status} ${response.config.method?.toUpperCase()} ${response.config.url}`);
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    const fullUrl = `${originalRequest?.baseURL || ''}${originalRequest?.url || ''}`;

    // Detailed diagnostic logging
    console.error(
      `❌ [API ERR] ${originalRequest?.method?.toUpperCase()} ${fullUrl} | ` +
      `Status: ${error.response?.status || 'No Response'} | ` +
      `Message: ${error.message} | Code: ${error.code || 'UNKNOWN'}`
    );

    if (error.response?.data) {
      console.error('   [API ERR Response Body]:', JSON.stringify(error.response.data));
    }

    if (error.message === 'Network Error') {
      console.error(
        `   [API Network Diagnostic]: Failed to reach backend at "${originalRequest?.baseURL}". ` +
        `Verify your phone is on the same Wi-Fi and that the backend IP (${API_CONFIG.BASE_URL}) is reachable.`
      );
    }

    if (error.response?.status === 401 && !originalRequest._retry) {
      const refreshToken = useAuthStore.getState().refreshToken;

      if (refreshToken && !originalRequest.url?.includes('/auth/login') && !originalRequest.url?.includes('/auth/refresh')) {
        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          })
            .then((token) => {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              return apiClient(originalRequest);
            })
            .catch((err) => Promise.reject(err));
        }

        originalRequest._retry = true;
        isRefreshing = true;

        try {
          console.log('🔄 [API] Attempting token refresh...');
          const res = await axios.post(`${API_CONFIG.BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          const newToken = res.data.access_token;
          const user = useAuthStore.getState().user;
          if (user) {
            await useAuthStore.getState().setAuth(newToken, user, refreshToken);
          }
          apiClient.defaults.headers.common.Authorization = `Bearer ${newToken}`;
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          processQueue(null, newToken);
          console.log('✅ [API] Token refresh succeeded.');
          return apiClient(originalRequest);
        } catch (refreshErr) {
          console.error('❌ [API] Token refresh failed:', refreshErr);
          processQueue(refreshErr, null);
          useAuthStore.getState().logout();
          return Promise.reject(refreshErr);
        } finally {
          isRefreshing = false;
        }
      } else {
        useAuthStore.getState().logout();
      }
    }
    return Promise.reject(error);
  }
);
