/**
 * React Query hooks for Homework system.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  createHomework,
  listHomework,
  getHomework,
  updateHomework,
  deleteHomework,
  publishHomework,
  closeHomework,
  addTask,
  deleteTask,
  addQuestion,
  generateQuestions,
  getReviewQueue,
  reviewAnswer,
  getTextbooks,
  getChapters,
  getParagraphs,
} from '@/lib/api/homework';
import type {
  HomeworkCreate,
  HomeworkUpdate,
  HomeworkListParams,
  HomeworkTaskCreate,
  QuestionCreate,
  GenerationParams,
  ReviewQueueParams,
  TeacherReviewRequest,
} from '@/types/homework';

// =============================================================================
// Query Keys
// =============================================================================

export const homeworkKeys = {
  all: ['homework'] as const,
  lists: () => [...homeworkKeys.all, 'list'] as const,
  list: (params?: HomeworkListParams) => [...homeworkKeys.lists(), params] as const,
  details: () => [...homeworkKeys.all, 'detail'] as const,
  detail: (id: number) => [...homeworkKeys.details(), id] as const,
  reviewQueue: (params?: ReviewQueueParams) => [...homeworkKeys.all, 'review-queue', params] as const,
  textbooks: () => ['textbooks'] as const,
  chapters: (textbookId: number) => ['textbooks', textbookId, 'chapters'] as const,
  paragraphs: (chapterId: number) => ['chapters', chapterId, 'paragraphs'] as const,
};

// =============================================================================
// Queries
// =============================================================================

export function useHomeworkList(params?: HomeworkListParams) {
  return useQuery({
    queryKey: homeworkKeys.list(params),
    queryFn: () => listHomework(params),
  });
}

export function useHomework(homeworkId: number) {
  return useQuery({
    queryKey: homeworkKeys.detail(homeworkId),
    queryFn: () => getHomework(homeworkId),
    enabled: !!homeworkId,
  });
}

export function useReviewQueue(params?: ReviewQueueParams) {
  return useQuery({
    queryKey: homeworkKeys.reviewQueue(params),
    queryFn: () => getReviewQueue(params),
  });
}

// Content queries for ContentSelector
export function useTextbooks() {
  return useQuery({
    queryKey: homeworkKeys.textbooks(),
    queryFn: getTextbooks,
  });
}

export function useChapters(textbookId: number) {
  return useQuery({
    queryKey: homeworkKeys.chapters(textbookId),
    queryFn: () => getChapters(textbookId),
    enabled: !!textbookId,
  });
}

export function useParagraphs(chapterId: number) {
  return useQuery({
    queryKey: homeworkKeys.paragraphs(chapterId),
    queryFn: () => getParagraphs(chapterId),
    enabled: !!chapterId,
  });
}

// =============================================================================
// Mutations
// =============================================================================

export function useCreateHomework() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: HomeworkCreate) => createHomework(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: homeworkKeys.lists() });
    },
  });
}

export function useUpdateHomework() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ homeworkId, data }: { homeworkId: number; data: HomeworkUpdate }) =>
      updateHomework(homeworkId, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: homeworkKeys.lists() });
      queryClient.setQueryData(homeworkKeys.detail(data.id), data);
    },
  });
}

export function useDeleteHomework() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (homeworkId: number) => deleteHomework(homeworkId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: homeworkKeys.lists() });
    },
  });
}

export function usePublishHomework() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ homeworkId, studentIds }: { homeworkId: number; studentIds?: number[] }) =>
      publishHomework(homeworkId, studentIds),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: homeworkKeys.lists() });
      queryClient.setQueryData(homeworkKeys.detail(data.id), data);
    },
  });
}

export function useCloseHomework() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (homeworkId: number) => closeHomework(homeworkId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: homeworkKeys.lists() });
      queryClient.setQueryData(homeworkKeys.detail(data.id), data);
    },
  });
}

// =============================================================================
// Task Mutations
// =============================================================================

export function useAddTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ homeworkId, data }: { homeworkId: number; data: HomeworkTaskCreate }) =>
      addTask(homeworkId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: homeworkKeys.detail(variables.homeworkId) });
    },
  });
}

export function useDeleteTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ taskId, homeworkId }: { taskId: number; homeworkId: number }) =>
      deleteTask(taskId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: homeworkKeys.detail(variables.homeworkId) });
    },
  });
}

// =============================================================================
// Question Mutations
// =============================================================================

export function useAddQuestion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      taskId,
      data,
      homeworkId,
    }: {
      taskId: number;
      data: QuestionCreate;
      homeworkId: number;
    }) => addQuestion(taskId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: homeworkKeys.detail(variables.homeworkId) });
    },
  });
}

export function useGenerateQuestions() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      taskId,
      params,
      regenerate,
      homeworkId,
    }: {
      taskId: number;
      params?: GenerationParams;
      regenerate?: boolean;
      homeworkId: number;
    }) => generateQuestions(taskId, params, regenerate),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: homeworkKeys.detail(variables.homeworkId) });
    },
  });
}

// =============================================================================
// Review Mutations
// =============================================================================

export function useReviewAnswer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ answerId, data }: { answerId: number; data: TeacherReviewRequest }) =>
      reviewAnswer(answerId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: homeworkKeys.reviewQueue() });
    },
  });
}
