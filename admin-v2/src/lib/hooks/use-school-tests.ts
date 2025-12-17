import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { schoolTestsApi } from '@/lib/api/school-tests';
import type { Test, TestCreate, TestUpdate, QuestionCreate, QuestionUpdate } from '@/types';
import { toast } from 'sonner';

// Query keys factory
export const schoolTestKeys = {
  all: ['school-tests'] as const,
  lists: () => [...schoolTestKeys.all, 'list'] as const,
  list: (filters?: Record<string, unknown>) => [...schoolTestKeys.lists(), filters] as const,
  details: () => [...schoolTestKeys.all, 'detail'] as const,
  detail: (id: number) => [...schoolTestKeys.details(), id] as const,
  questions: (testId: number) => [...schoolTestKeys.detail(testId), 'questions'] as const,
};

// Get all tests
export function useSchoolTests() {
  return useQuery({
    queryKey: schoolTestKeys.lists(),
    queryFn: schoolTestsApi.getList,
  });
}

// Get single test by ID
export function useSchoolTest(id: number, enabled = true) {
  return useQuery({
    queryKey: schoolTestKeys.detail(id),
    queryFn: () => schoolTestsApi.getOne(id),
    enabled: enabled && id > 0,
  });
}

// Create test mutation
export function useCreateSchoolTest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TestCreate) => schoolTestsApi.create(data),
    onSuccess: (newTest) => {
      queryClient.invalidateQueries({ queryKey: schoolTestKeys.lists() });
      toast.success(`Тест "${newTest.title}" создан`);
    },
    onError: (error: Error) => {
      toast.error(`Ошибка создания: ${error.message}`);
    },
  });
}

// Update test mutation
export function useUpdateSchoolTest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: TestUpdate }) =>
      schoolTestsApi.update(id, data),
    onSuccess: (updatedTest) => {
      queryClient.invalidateQueries({ queryKey: schoolTestKeys.lists() });
      queryClient.invalidateQueries({
        queryKey: schoolTestKeys.detail(updatedTest.id),
      });
      toast.success(`Тест "${updatedTest.title}" обновлен`);
    },
    onError: (error: Error) => {
      toast.error(`Ошибка обновления: ${error.message}`);
    },
  });
}

// Delete test mutation
export function useDeleteSchoolTest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => schoolTestsApi.delete(id),
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({ queryKey: schoolTestKeys.lists() });
      queryClient.removeQueries({ queryKey: schoolTestKeys.detail(deletedId) });
      toast.success('Тест удален');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка удаления: ${error.message}`);
    },
  });
}

// Get questions for test
export function useSchoolTestQuestions(testId: number, enabled = true) {
  return useQuery({
    queryKey: schoolTestKeys.questions(testId),
    queryFn: () => schoolTestsApi.getQuestions(testId),
    enabled: enabled && testId > 0,
  });
}

// Create question mutation
export function useCreateSchoolQuestion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ testId, data }: { testId: number; data: QuestionCreate }) =>
      schoolTestsApi.createQuestion(testId, data),
    onSuccess: (_, { testId }) => {
      queryClient.invalidateQueries({ queryKey: schoolTestKeys.questions(testId) });
      toast.success('Вопрос добавлен');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка создания: ${error.message}`);
    },
  });
}

// Update question mutation
export function useUpdateSchoolQuestion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ questionId, testId, data }: { questionId: number; testId: number; data: QuestionUpdate }) =>
      schoolTestsApi.updateQuestion(questionId, data),
    onSuccess: (_, { testId }) => {
      queryClient.invalidateQueries({ queryKey: schoolTestKeys.questions(testId) });
      toast.success('Вопрос обновлен');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка обновления: ${error.message}`);
    },
  });
}

// Delete question mutation
export function useDeleteSchoolQuestion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ questionId, testId }: { questionId: number; testId: number }) =>
      schoolTestsApi.deleteQuestion(questionId),
    onSuccess: (_, { testId }) => {
      queryClient.invalidateQueries({ queryKey: schoolTestKeys.questions(testId) });
      toast.success('Вопрос удален');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка удаления: ${error.message}`);
    },
  });
}
