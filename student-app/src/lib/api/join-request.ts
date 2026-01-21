import { apiClient } from './client';

// =============================================================================
// Types - matching backend schemas
// =============================================================================

export interface JoinRequestCreateData {
  invitation_code: string;
  first_name: string;
  last_name: string;
  middle_name?: string;
}

export interface JoinRequestResponse {
  id: number;
  student_id: number;
  class_id: number;
  school_id: number;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
}

export interface JoinRequestStatus {
  id: number | null;
  status: 'pending' | 'approved' | 'rejected' | null;
  class_name: string | null;
  school_name: string | null;
  created_at: string | null;
  rejection_reason: string | null;
  has_request: boolean;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Create a join request to a class using invitation code.
 */
export async function createJoinRequest(
  data: JoinRequestCreateData
): Promise<JoinRequestResponse> {
  const response = await apiClient.post<JoinRequestResponse>(
    '/students/join-request',
    data
  );
  return response.data;
}

/**
 * Get current join request status.
 */
export async function getJoinRequestStatus(): Promise<JoinRequestStatus> {
  const response = await apiClient.get<JoinRequestStatus>(
    '/students/join-request/status'
  );
  return response.data;
}
