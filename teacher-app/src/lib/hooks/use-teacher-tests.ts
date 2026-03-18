import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { teacherTestsApi } from '@/lib/api/teacher-tests';
import type { TestCreate, TestUpdate, QuestionCreate, QuestionUpdate } from '@/types/test';
import { toast } from 'sonner';

// Query keys factory
export const teacherTestKeys = {
  all: ['teacher-tests'] as const,
  lists: () => [...teacherTestKeys.all, 'list'] as const,
  list: (filters?: Record<string, unknown>) => [...teacherTestKeys.lists(), filters] as const,
  details: () => [...teacherTestKeys.all, 'detail'] as const,
  detail: (id: number) => [...teacherTestKeys.details(), id] as const,
  questions: (testId: number) => [...teacherTestKeys.detail(testId), 'questions'] as const,
};

// Get all tests
export function useTeacherTests(params?: { include_global?: boolean; chapter_id?: number; grade_level?: number; page_size?: number }) {
  return useQuery({
    queryKey: teacherTestKeys.list(params as Record<string, unknown>),
    queryFn: () => teacherTestsApi.getList(params),
  });
}

// Get single test by ID
export function useTeacherTest(id: number, enabled = true) {
  return useQuery({
    queryKey: teacherTestKeys.detail(id),
    queryFn: () => teacherTestsApi.getOne(id),
    enabled: enabled && id > 0,
  });
}

// Create test mutation
export function useCreateTeacherTest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TestCreate) => teacherTestsApi.create(data),
    onSuccess: (newTest) => {
      queryClient.invalidateQueries({ queryKey: teacherTestKeys.lists() });
      toast.success(`Тест "${newTest.title}" создан`);
    },
    onError: (error: Error) => {
      toast.error(`Ошибка создания: ${error.message}`);
    },
  });
}

// Update test mutation
export function useUpdateTeacherTest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: TestUpdate }) =>
      teacherTestsApi.update(id, data),
    onSuccess: (updatedTest) => {
      queryClient.invalidateQueries({ queryKey: teacherTestKeys.lists() });
      queryClient.invalidateQueries({
        queryKey: teacherTestKeys.detail(updatedTest.id),
      });
      toast.success(`Тест "${updatedTest.title}" обновлен`);
    },
    onError: (error: Error) => {
      toast.error(`Ошибка обновления: ${error.message}`);
    },
  });
}

// Delete test mutation
export function useDeleteTeacherTest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => teacherTestsApi.delete(id),
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({ queryKey: teacherTestKeys.lists() });
      queryClient.removeQueries({ queryKey: teacherTestKeys.detail(deletedId) });
      toast.success('Тест удален');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка удаления: ${error.message}`);
    },
  });
}

// Get questions for test
export function useTeacherTestQuestions(testId: number, enabled = true) {
  return useQuery({
    queryKey: teacherTestKeys.questions(testId),
    queryFn: () => teacherTestsApi.getQuestions(testId),
    enabled: enabled && testId > 0,
  });
}

// Create question mutation
export function useCreateTeacherQuestion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ testId, data }: { testId: number; data: QuestionCreate }) =>
      teacherTestsApi.createQuestion(testId, data),
    onSuccess: (_, { testId }) => {
      queryClient.invalidateQueries({ queryKey: teacherTestKeys.questions(testId) });
      toast.success('Вопрос добавлен');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка создания: ${error.message}`);
    },
  });
}

// Update question mutation
export function useUpdateTeacherQuestion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ questionId, testId, data }: { questionId: number; testId: number; data: QuestionUpdate }) =>
      teacherTestsApi.updateQuestion(questionId, data),
    onSuccess: (_, { testId }) => {
      queryClient.invalidateQueries({ queryKey: teacherTestKeys.questions(testId) });
      toast.success('Вопрос обновлен');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка обновления: ${error.message}`);
    },
  });
}

// Delete question mutation
export function useDeleteTeacherQuestion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ questionId, testId }: { questionId: number; testId: number }) =>
      teacherTestsApi.deleteQuestion(questionId),
    onSuccess: (_, { testId }) => {
      queryClient.invalidateQueries({ queryKey: teacherTestKeys.questions(testId) });
      toast.success('Вопрос удален');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка удаления: ${error.message}`);
    },
  });
}
