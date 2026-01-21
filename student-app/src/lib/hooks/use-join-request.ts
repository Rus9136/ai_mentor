import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  createJoinRequest,
  getJoinRequestStatus,
  JoinRequestCreateData,
  JoinRequestResponse,
  JoinRequestStatus,
} from '@/lib/api/join-request';

// =============================================================================
// Query Keys Factory
// =============================================================================

export const joinRequestKeys = {
  all: ['joinRequest'] as const,
  status: () => [...joinRequestKeys.all, 'status'] as const,
};

// =============================================================================
// Hooks
// =============================================================================

/**
 * Hook to get current join request status.
 */
export function useJoinRequestStatus() {
  return useQuery<JoinRequestStatus, Error>({
    queryKey: joinRequestKeys.status(),
    queryFn: getJoinRequestStatus,
    staleTime: 1000 * 60 * 2, // 2 minutes
  });
}

/**
 * Hook to create a join request.
 */
export function useCreateJoinRequest() {
  const queryClient = useQueryClient();

  return useMutation<JoinRequestResponse, Error, JoinRequestCreateData>({
    mutationFn: createJoinRequest,
    onSuccess: () => {
      // Invalidate join request status to refetch
      queryClient.invalidateQueries({ queryKey: joinRequestKeys.status() });
    },
  });
}
