import { useQuery } from '@tanstack/react-query';
import {
  getStudentStats,
  getMasteryOverview,
  getStudentProfile,
  getMetacognitiveInsight,
  StudentStats,
  MasteryOverview,
  StudentProfile,
  MetacognitiveInsight,
} from '@/lib/api/profile';

// =============================================================================
// Query Keys Factory
// =============================================================================

export const profileKeys = {
  all: ['profile'] as const,
  stats: () => [...profileKeys.all, 'stats'] as const,
  mastery: () => [...profileKeys.all, 'mastery'] as const,
  student: () => [...profileKeys.all, 'student'] as const,
  metacognitive: (lang: string) => [...profileKeys.all, 'metacognitive', lang] as const,
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

/**
 * Hook to get student's profile with class information.
 */
export function useStudentProfile() {
  return useQuery<StudentProfile, Error>({
    queryKey: profileKeys.student(),
    queryFn: getStudentProfile,
    staleTime: 1000 * 60 * 10, // 10 minutes
  });
}

/**
 * Hook to get student's metacognitive pattern and coaching message.
 */
export function useMetacognitiveInsight(lang: string = 'ru') {
  return useQuery<MetacognitiveInsight, Error>({
    queryKey: profileKeys.metacognitive(lang),
    queryFn: () => getMetacognitiveInsight(lang),
    staleTime: 1000 * 60 * 10, // 10 minutes
  });
}
