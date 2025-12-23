import { apiClient, setTokens, clearTokens } from './client';

export interface GoogleAuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  requires_onboarding: boolean;
  user: {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
    avatar_url: string | null;
    role: string;
    school_id: number | null;
  };
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

// Google OAuth login
export async function googleAuth(idToken: string): Promise<GoogleAuthResponse> {
  const response = await apiClient.post<GoogleAuthResponse>('/auth/google', {
    id_token: idToken,
  });

  // Only allow teachers
  if (response.data.user.role !== 'teacher') {
    throw new Error('ACCESS_DENIED');
  }

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
