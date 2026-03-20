/**
 * React Query hooks for Coding Challenges & Courses
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  listTopics,
  listChallenges,
  getChallengeDetail,
  submitSolution,
  listSubmissions,
  getCodingStats,
  listCourses,
  listLessons,
  getLessonDetail,
  completeLesson,
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
  // Courses
  courses: () => [...codingKeys.all, 'courses'] as const,
  lessons: (slug: string) =>
    [...codingKeys.all, 'lessons', slug] as const,
  lessonDetail: (id: number) =>
    [...codingKeys.all, 'lesson', id] as const,
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

// =============================================================================
// Course Queries
// =============================================================================

export function useCodingCourses() {
  return useQuery({
    queryKey: codingKeys.courses(),
    queryFn: listCourses,
    staleTime: 5 * 60 * 1000,
  });
}

export function useCourseLessons(courseSlug: string) {
  return useQuery({
    queryKey: codingKeys.lessons(courseSlug),
    queryFn: () => listLessons(courseSlug),
    enabled: !!courseSlug,
    staleTime: 60 * 1000,
  });
}

export function useLessonDetail(lessonId: number | undefined) {
  return useQuery({
    queryKey: codingKeys.lessonDetail(lessonId!),
    queryFn: () => getLessonDetail(lessonId!),
    enabled: !!lessonId,
    staleTime: 30 * 1000,
  });
}

// =============================================================================
// Course Mutations
// =============================================================================

export function useCompleteLesson(lessonId: number, courseSlug: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => completeLesson(lessonId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: codingKeys.lessonDetail(lessonId),
      });
      queryClient.invalidateQueries({
        queryKey: codingKeys.lessons(courseSlug),
      });
      queryClient.invalidateQueries({
        queryKey: codingKeys.courses(),
      });
    },
  });
}
