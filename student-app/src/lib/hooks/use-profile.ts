import { useQuery } from '@tanstack/react-query';
import {
  getStudentStats,
  getMasteryOverview,
  StudentStats,
  MasteryOverview,
} from '@/lib/api/profile';

// =============================================================================
// Query Keys Factory
// =============================================================================

export const profileKeys = {
  all: ['profile'] as const,
  stats: () => [...profileKeys.all, 'stats'] as const,
  mastery: () => [...profileKeys.all, 'mastery'] as const,
};

// =============================================================================
// Hooks
// =============================================================================

/**
 * Hook to get student's overall stats (streak, paragraphs, tasks, time).
 */
export function useStudentStats() {
  return useQuery<StudentStats, Error>({
    queryKey: profileKeys.stats(),
    queryFn: getStudentStats,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

/**
 * Hook to get mastery overview across all chapters.
 */
export function useMasteryOverview() {
  return useQuery<MasteryOverview, Error>({
    queryKey: profileKeys.mastery(),
    queryFn: getMasteryOverview,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}
