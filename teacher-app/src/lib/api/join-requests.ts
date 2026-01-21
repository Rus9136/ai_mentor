import { apiClient } from './client';

export interface PendingRequestCount {
  class_id: number;
  class_name: string;
  pending_count: number;
}

export interface JoinRequestDetail {
  id: number;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
  student_id: number;
  student_code: string;
  student_first_name: string;
  student_last_name: string;
  student_middle_name: string | null;
  student_email: string | null;
  student_grade_level: number;
  class_id: number;
  class_name: string;
  invitation_code: string | null;
}

export interface JoinRequestActionResponse {
  id: number;
  status: string;
  reviewed_at: string;
  message: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

/**
 * Get pending request counts for all teacher's classes
 */
export async function getPendingCounts(): Promise<PendingRequestCount[]> {
  const response = await apiClient.get<PendingRequestCount[]>(
    '/teachers/join-requests/pending-counts'
  );
  return response.data;
}

/**
 * Get pending requests for a specific class
 */
export async function getClassPendingRequests(
  classId: number,
  page: number = 1,
  pageSize: number = 20
): Promise<PaginatedResponse<JoinRequestDetail>> {
  const response = await apiClient.get<PaginatedResponse<JoinRequestDetail>>(
    `/teachers/join-requests/classes/${classId}`,
    {
      params: { page, page_size: pageSize },
    }
  );
  return response.data;
}

/**
 * Approve a join request
 */
export async function approveJoinRequest(
  requestId: number
): Promise<JoinRequestActionResponse> {
  const response = await apiClient.post<JoinRequestActionResponse>(
    `/teachers/join-requests/${requestId}/approve`,
    {}
  );
  return response.data;
}

/**
 * Reject a join request
 */
export async function rejectJoinRequest(
  requestId: number,
  reason?: string
): Promise<JoinRequestActionResponse> {
  const response = await apiClient.post<JoinRequestActionResponse>(
    `/teachers/join-requests/${requestId}/reject`,
    { reason }
  );
  return response.data;
}
