import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getDueReviews, completeReview, getReviewStats } from '@/lib/api/reviews';

/**
 * Get reviews due for today.
 */
export function useDueReviews() {
  return useQuery({
    queryKey: ['reviews', 'due'],
    queryFn: getDueReviews,
    staleTime: 2 * 60 * 1000,
  });
}

/**
 * Submit review result.
 */
export function useCompleteReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ paragraphId, score }: { paragraphId: number; score: number }) =>
      completeReview(paragraphId, score),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reviews'] });
    },
  });
}

/**
 * Get spaced repetition stats.
 */
export function useReviewStats() {
  return useQuery({
    queryKey: ['reviews', 'stats'],
    queryFn: getReviewStats,
    staleTime: 5 * 60 * 1000,
  });
}
