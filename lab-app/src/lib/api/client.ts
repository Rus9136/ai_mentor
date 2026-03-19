import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import type { APIError } from '@/types/error';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.ai-mentor.kz/api/v1';
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://api.ai-mentor.kz';

export const getMediaUrl = (path: string | null | undefined): string | null => {
  if (!path) return null;
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  return `${API_BASE_URL}${path}`;
};

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token storage keys (unique for lab-app)
const ACCESS_TOKEN_KEY = 'ai_mentor_lab_access_token';
const REFRESH_TOKEN_KEY = 'ai_mentor_lab_refresh_token';

// Also check student-app tokens (shared auth)
const STUDENT_ACCESS_TOKEN_KEY = 'ai_mentor_access_token';
const STUDENT_REFRESH_TOKEN_KEY = 'ai_mentor_refresh_token';

export const getAccessToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  // Try lab-app tokens first, then fall back to student-app tokens (shared session)
  return localStorage.getItem(ACCESS_TOKEN_KEY)
    || localStorage.getItem(STUDENT_ACCESS_TOKEN_KEY);
};

export const getRefreshToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY)
    || localStorage.getItem(STUDENT_REFRESH_TOKEN_KEY);
};

export const setTokens = (accessToken: string, refreshToken: string): void => {
  if (typeof window === 'undefined') return;
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
};

export const clearTokens = (): void => {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
};

// Request interceptor - add auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle token refresh
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: AxiosError) => void;
}> = [];

const processQueue = (error: AxiosError | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else if (token) {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
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

      const refreshToken = getRefreshToken();
      if (!refreshToken) {
        // In WebView context mobile app manages tokens — don't redirect
        const isWebView = typeof window !== 'undefined' && window.location.pathname.includes('/webview/');
        if (!isWebView) {
          clearTokens();
          window.location.href = '/ru/login';
        }
        return Promise.reject(error);
      }

      try {
        const response = await axios.post(`${API_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const { access_token, refresh_token } = response.data;
        setTokens(access_token, refresh_token);

        processQueue(null, access_token);
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError as AxiosError, null);
        clearTokens();
        const isWebView = typeof window !== 'undefined' && window.location.pathname.includes('/webview/');
        if (!isWebView) {
          window.location.href = '/ru/login';
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export function getAPIError(error: unknown): APIError {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data;

    if (data && typeof data === 'object' && 'code' in data) {
      return data as APIError;
    }

    if (data && typeof data.detail === 'string') {
      return { code: 'UNKNOWN', message: data.detail, detail: data.detail };
    }

    return { code: 'NETWORK_ERROR', message: error.message || 'Network error', detail: error.message || 'Network error' };
  }

  if (error instanceof Error) {
    return { code: 'UNKNOWN', message: error.message, detail: error.message };
  }

  return { code: 'UNKNOWN', message: 'Unknown error', detail: 'Unknown error' };
}

export function getErrorMessage(error: unknown): string {
  return getAPIError(error).message;
}
