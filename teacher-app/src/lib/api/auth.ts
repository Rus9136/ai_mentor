import { apiClient, setTokens, clearTokens } from './client';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserResponse {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  middle_name: string | null;
  role: string;
  school_id: number | null;
  avatar_url: string | null;
  auth_provider: string;
  is_active: boolean;
  is_verified: boolean;
}

// Email/Password login
export async function login(credentials: LoginCredentials): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>('/auth/login', credentials);

  // Save tokens
  setTokens(response.data.access_token, response.data.refresh_token);

  return response.data;
}

// Get current user
export async function getCurrentUser(): Promise<UserResponse> {
  const response = await apiClient.get<UserResponse>('/auth/me');
  return response.data;
}

// Logout
export function logout(): void {
  clearTokens();
}

// Get error message from API response
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    // Check if it's an Axios error with response
    const axiosError = error as { response?: { data?: { detail?: string } } };
    if (axiosError.response?.data?.detail) {
      return axiosError.response.data.detail;
    }
    return error.message;
  }
  return 'Произошла неизвестная ошибка';
}
