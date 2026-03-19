import { apiClient, setTokens, clearTokens } from './client';

export interface LoginCredentials {
  email: string;
  password: string;
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

export async function getCurrentUser(): Promise<UserResponse> {
  const response = await apiClient.get<UserResponse>('/auth/me');
  return response.data;
}

export async function loginWithPassword(credentials: LoginCredentials): Promise<void> {
  const response = await apiClient.post('/auth/login', credentials);
  setTokens(response.data.access_token, response.data.refresh_token);
}

export function logout(): void {
  clearTokens();
}
