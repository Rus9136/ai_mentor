/**
 * React Query hooks for Coding Challenges
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  listTopics,
  listChallenges,
  getChallengeDetail,
  submitSolution,
  listSubmissions,
  getCodingStats,
  type SubmitSolutionRequest,
} from '@/lib/api/coding';

// =============================================================================
// Query Keys
// =============================================================================

export const codingKeys = {
  all: ['coding'] as const,
  topics: () => [...codingKeys.all, 'topics'] as const,
  challenges: (slug: string) =>
    [...codingKeys.all, 'challenges', slug] as const,
  detail: (id: number) => [...codingKeys.all, 'detail', id] as const,
  submissions: (id: number) =>
    [...codingKeys.all, 'submissions', id] as const,
  stats: () => [...codingKeys.all, 'stats'] as const,
};

// =============================================================================
// Queries
// =============================================================================

export function useCodingTopics() {
  return useQuery({
    queryKey: codingKeys.topics(),
    queryFn: listTopics,
    staleTime: 5 * 60 * 1000,
  });
}

export function useChallenges(topicSlug: string) {
  return useQuery({
    queryKey: codingKeys.challenges(topicSlug),
    queryFn: () => listChallenges(topicSlug),
    enabled: !!topicSlug,
    staleTime: 60 * 1000,
  });
}

export function useChallengeDetail(challengeId: number | undefined) {
  return useQuery({
    queryKey: codingKeys.detail(challengeId!),
    queryFn: () => getChallengeDetail(challengeId!),
    enabled: !!challengeId,
    staleTime: 30 * 1000,
  });
}

export function useChallengeSubmissions(challengeId: number | undefined) {
  return useQuery({
    queryKey: codingKeys.submissions(challengeId!),
    queryFn: () => listSubmissions(challengeId!),
    enabled: !!challengeId,
    staleTime: 30 * 1000,
  });
}

export function useCodingStats() {
  return useQuery({
    queryKey: codingKeys.stats(),
    queryFn: getCodingStats,
    staleTime: 60 * 1000,
  });
}

// =============================================================================
// Mutations
// =============================================================================

export function useSubmitSolution(challengeId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SubmitSolutionRequest) =>
      submitSolution(challengeId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: codingKeys.detail(challengeId),
      });
      queryClient.invalidateQueries({
        queryKey: codingKeys.submissions(challengeId),
      });
      queryClient.invalidateQueries({
        queryKey: codingKeys.topics(),
      });
      queryClient.invalidateQueries({
        queryKey: codingKeys.stats(),
      });
    },
  });
}
