import { apiClient, setTokens, clearTokens } from './client';

export interface GoogleAuthRequest {
  id_token: string;
}

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

export interface ValidateCodeRequest {
  code: string;
}

export interface ValidateCodeResponse {
  valid: boolean;
  school_name?: string;
  class_name?: string;
  grade_level?: number;
  message?: string;
}

export interface OnboardingCompleteRequest {
  code: string;
  first_name: string;
  last_name: string;
  middle_name?: string;
  birth_date?: string;
}

export interface OnboardingCompleteResponse {
  success: boolean;
  message: string;
  student_code: string;
  access_token: string;
  refresh_token: string;
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

  // Save tokens
  setTokens(response.data.access_token, response.data.refresh_token);

  return response.data;
}

// Validate invitation code
export async function validateCode(code: string): Promise<ValidateCodeResponse> {
  const response = await apiClient.post<ValidateCodeResponse>(
    '/auth/onboarding/validate-code',
    { code }
  );
  return response.data;
}

// Complete onboarding
export async function completeOnboarding(
  data: OnboardingCompleteRequest
): Promise<OnboardingCompleteResponse> {
  const response = await apiClient.post<OnboardingCompleteResponse>(
    '/auth/onboarding/complete',
    data
  );

  // Update tokens with new ones that include school_id
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
