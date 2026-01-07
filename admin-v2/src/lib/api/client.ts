import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import type { APIError } from '@/types/error';

// Use relative URL in browser (proxied by Next.js rewrites to avoid CORS)
// Use full URL on server side
const API_URL = typeof window !== 'undefined'
  ? '/api/v1'  // Browser: proxied through Next.js
  : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1');

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle 401 and token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
          throw new Error('No refresh token');
        }

        const response = await axios.post(`${API_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const { access_token, refresh_token: newRefresh } = response.data;
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', newRefresh);

        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');

        // Redirect to login - get current locale from URL
        if (typeof window !== 'undefined') {
          const locale = window.location.pathname.split('/')[1] || 'ru';
          window.location.href = `/${locale}/login`;
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

/**
 * Extract structured API error from response.
 *
 * Handles both new structured format (with code) and legacy string format.
 */
export function getAPIError(error: unknown): APIError {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data;

    // New structured format (has code field)
    if (data && typeof data === 'object' && 'code' in data) {
      return data as APIError;
    }

    // Legacy string format (just detail field)
    if (data && typeof data.detail === 'string') {
      return {
        code: 'UNKNOWN',
        message: data.detail,
        detail: data.detail,
      };
    }

    // Network or other axios error
    return {
      code: 'NETWORK_ERROR',
      message: error.message || 'Network error',
      detail: error.message || 'Network error',
    };
  }

  // Generic error
  if (error instanceof Error) {
    return {
      code: 'UNKNOWN',
      message: error.message,
      detail: error.message,
    };
  }

  return {
    code: 'UNKNOWN',
    message: 'Unknown error',
    detail: 'Unknown error',
  };
}

/**
 * Get localized error message using i18n translation function.
 *
 * @param error - The API error object
 * @param t - Translation function (from useTranslations)
 * @returns Localized error message, falls back to API message if key not found
 */
export function getLocalizedError(error: APIError, t: (key: string) => string): string {
  // Try i18n key: errors.AUTH_001
  const i18nKey = `errors.${error.code}`;
  const localized = t(i18nKey);

  // If translation returns the key itself, it wasn't found
  if (localized === i18nKey) {
    return error.message;
  }

  return localized;
}

/**
 * Helper to get error message from API response.
 *
 * @deprecated Use getAPIError() for structured error handling
 */
export function getErrorMessage(error: unknown): string {
  const apiError = getAPIError(error);
  return apiError.message;
}
