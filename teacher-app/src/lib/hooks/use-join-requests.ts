import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  getPendingCounts,
  getClassPendingRequests,
  approveJoinRequest,
  rejectJoinRequest,
} from '@/lib/api/join-requests';

/**
 * Hook to get pending request counts for teacher's classes
 */
export function usePendingCounts() {
  return useQuery({
    queryKey: ['teacher', 'join-requests', 'counts'],
    queryFn: getPendingCounts,
    refetchInterval: 60000, // Refetch every minute
  });
}

/**
 * Hook to get pending requests for a specific class
 */
export function useClassPendingRequests(classId: number, page: number = 1) {
  return useQuery({
    queryKey: ['teacher', 'join-requests', 'class', classId, page],
    queryFn: () => getClassPendingRequests(classId, page),
    enabled: !!classId,
  });
}

/**
 * Hook to approve a join request
 */
export function useApproveRequest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: approveJoinRequest,
    onSuccess: () => {
      toast.success('Заявка одобрена');
      queryClient.invalidateQueries({ queryKey: ['teacher', 'join-requests'] });
      queryClient.invalidateQueries({ queryKey: ['teacher', 'classes'] });
    },
    onError: () => {
      toast.error('Ошибка при одобрении заявки');
    },
  });
}

/**
 * Hook to reject a join request
 */
export function useRejectRequest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ requestId, reason }: { requestId: number; reason?: string }) =>
      rejectJoinRequest(requestId, reason),
    onSuccess: () => {
      toast.success('Заявка отклонена');
      queryClient.invalidateQueries({ queryKey: ['teacher', 'join-requests'] });
    },
    onError: () => {
      toast.error('Ошибка при отклонении заявки');
    },
  });
}
