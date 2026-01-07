/**
 * React Query hooks for Student Homework
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  listMyHomework,
  getHomeworkDetail,
  startTask,
  getTaskQuestions,
  submitAnswer,
  completeSubmission,
  getSubmissionResults,
  type HomeworkListParams,
  type AnswerSubmit,
} from '@/lib/api/homework';

// =============================================================================
// Query Keys Factory
// =============================================================================

export const homeworkKeys = {
  all: ['student-homework'] as const,
  lists: () => [...homeworkKeys.all, 'list'] as const,
  list: (params?: HomeworkListParams) =>
    [...homeworkKeys.lists(), params] as const,
  details: () => [...homeworkKeys.all, 'detail'] as const,
  detail: (id: number) => [...homeworkKeys.details(), id] as const,
  taskQuestions: (homeworkId: number, taskId: number) =>
    [...homeworkKeys.all, 'task', homeworkId, taskId, 'questions'] as const,
  submissionResults: (submissionId: number) =>
    [...homeworkKeys.all, 'submission', submissionId, 'results'] as const,
};

// =============================================================================
// Queries
// =============================================================================

export function useMyHomework(params?: HomeworkListParams) {
  return useQuery({
    queryKey: homeworkKeys.list(params),
    queryFn: () => listMyHomework(params),
    staleTime: 60 * 1000,
  });
}

export function useHomeworkDetail(homeworkId: number | undefined) {
  return useQuery({
    queryKey: homeworkKeys.detail(homeworkId!),
    queryFn: () => getHomeworkDetail(homeworkId!),
    enabled: !!homeworkId,
    staleTime: 30 * 1000,
  });
}

export function useTaskQuestions(
  homeworkId: number | undefined,
  taskId: number | undefined
) {
  return useQuery({
    queryKey: homeworkKeys.taskQuestions(homeworkId!, taskId!),
    queryFn: () => getTaskQuestions(homeworkId!, taskId!),
    enabled: !!homeworkId && !!taskId,
    staleTime: 30 * 1000,
  });
}

export function useSubmissionResults(submissionId: number | undefined) {
  return useQuery({
    queryKey: homeworkKeys.submissionResults(submissionId!),
    queryFn: () => getSubmissionResults(submissionId!),
    enabled: !!submissionId,
    staleTime: 60 * 1000,
  });
}

// =============================================================================
// Mutations
// =============================================================================

export function useStartTask(homeworkId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (taskId: number) => startTask(homeworkId, taskId),
    onSuccess: () => {
      // Invalidate homework detail to refresh task status
      queryClient.invalidateQueries({
        queryKey: homeworkKeys.detail(homeworkId),
      });
    },
  });
}

export function useSubmitAnswer() {
  return useMutation({
    mutationFn: ({
      submissionId,
      data,
    }: {
      submissionId: number;
      data: AnswerSubmit;
    }) => submitAnswer(submissionId, data),
  });
}

export function useCompleteSubmission(homeworkId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (submissionId: number) => completeSubmission(submissionId),
    onSuccess: () => {
      // Invalidate homework detail to refresh task status
      queryClient.invalidateQueries({
        queryKey: homeworkKeys.detail(homeworkId),
      });
      // Invalidate lists to update overall status
      queryClient.invalidateQueries({
        queryKey: homeworkKeys.lists(),
      });
    },
  });
}
