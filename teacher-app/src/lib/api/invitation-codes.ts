import { apiClient } from './client';

// ============================================================================
// Types
// ============================================================================

export interface InvitationCode {
  id: number;
  code: string;
  school_id: number;
  class_id: number | null;
  class_name: string | null;
  grade_level: number;
  expires_at: string | null;
  max_uses: number | null;
  uses_count: number;
  is_active: boolean;
  created_by: number;
  created_by_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateInvitationCodeData {
  expires_at?: string | null;
  max_uses?: number | null;
  code_prefix?: string | null;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Get invitation codes for a class.
 */
export async function getClassInvitationCodes(
  classId: number,
  isActive?: boolean
): Promise<InvitationCode[]> {
  const params = new URLSearchParams();
  if (isActive !== undefined) {
    params.append('is_active', String(isActive));
  }

  const url = `/teachers/classes/${classId}/invitation-codes${params.toString() ? `?${params.toString()}` : ''}`;
  const response = await apiClient.get<InvitationCode[]>(url);
  return response.data;
}

/**
 * Create a new invitation code for a class.
 */
export async function createInvitationCode(
  classId: number,
  data: CreateInvitationCodeData
): Promise<InvitationCode> {
  const response = await apiClient.post<InvitationCode>(
    `/teachers/classes/${classId}/invitation-codes`,
    {
      grade_level: 7, // Will be overridden by backend from class
      ...data,
    }
  );
  return response.data;
}

/**
 * Deactivate an invitation code.
 */
export async function deactivateInvitationCode(
  classId: number,
  codeId: number
): Promise<void> {
  await apiClient.delete(`/teachers/classes/${classId}/invitation-codes/${codeId}`);
}
