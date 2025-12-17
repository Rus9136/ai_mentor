import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { testsApi } from '@/lib/api/tests';
import type {
  Test,
  TestCreate,
  TestUpdate,
  Question,
  QuestionCreate,
  QuestionUpdate,
} from '@/types';
import { toast } from 'sonner';

// ==================== Tests ====================

export const testKeys = {
  all: ['tests'] as const,
  lists: () => [...testKeys.all, 'list'] as const,
  list: (isSchool: boolean, chapterId?: number) =>
    [...testKeys.lists(), { isSchool, chapterId }] as const,
  details: () => [...testKeys.all, 'detail'] as const,
  detail: (id: number, isSchool: boolean) =>
    [...testKeys.details(), id, { isSchool }] as const,
};

export function useTests(isSchool = false, chapterId?: number) {
  return useQuery({
    queryKey: testKeys.list(isSchool, chapterId),
    queryFn: () => testsApi.getList(isSchool, chapterId),
  });
}

export function useTest(id: number, isSchool = false, enabled = true) {
  return useQuery({
    queryKey: testKeys.detail(id, isSchool),
    queryFn: () => testsApi.getOne(id, isSchool),
    enabled: enabled && id > 0,
  });
}

export function useCreateTest(isSchool = false) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TestCreate) => testsApi.create(data, isSchool),
    onSuccess: (newTest) => {
      queryClient.invalidateQueries({ queryKey: testKeys.lists() });
      toast.success(`Тест "${newTest.title}" создан`);
    },
    onError: (error: Error) => {
      toast.error(`Ошибка создания: ${error.message}`);
    },
  });
}

export function useUpdateTest(isSchool = false) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: TestUpdate }) =>
      testsApi.update(id, data, isSchool),
    onSuccess: (updatedTest) => {
      queryClient.invalidateQueries({ queryKey: testKeys.lists() });
      queryClient.invalidateQueries({
        queryKey: testKeys.detail(updatedTest.id, isSchool),
      });
      toast.success(`Тест "${updatedTest.title}" обновлен`);
    },
    onError: (error: Error) => {
      toast.error(`Ошибка обновления: ${error.message}`);
    },
  });
}

export function useDeleteTest(isSchool = false) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => testsApi.delete(id, isSchool),
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({ queryKey: testKeys.lists() });
      queryClient.removeQueries({
        queryKey: testKeys.detail(deletedId, isSchool),
      });
      toast.success('Тест удален');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка удаления: ${error.message}`);
    },
  });
}

// ==================== Questions ====================

export const questionKeys = {
  all: ['questions'] as const,
  lists: () => [...questionKeys.all, 'list'] as const,
  list: (testId: number, isSchool: boolean) =>
    [...questionKeys.lists(), { testId, isSchool }] as const,
  details: () => [...questionKeys.all, 'detail'] as const,
  detail: (id: number, isSchool: boolean) =>
    [...questionKeys.details(), id, { isSchool }] as const,
};

export function useQuestions(testId: number, isSchool = false, enabled = true) {
  return useQuery({
    queryKey: questionKeys.list(testId, isSchool),
    queryFn: () => testsApi.getQuestions(testId, isSchool),
    enabled: enabled && testId > 0,
  });
}

export function useQuestion(questionId: number, isSchool = false, enabled = true) {
  return useQuery({
    queryKey: questionKeys.detail(questionId, isSchool),
    queryFn: () => testsApi.getQuestion(questionId, isSchool),
    enabled: enabled && questionId > 0,
  });
}

export function useCreateQuestion(isSchool = false) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ testId, data }: { testId: number; data: QuestionCreate }) =>
      testsApi.createQuestion(testId, data, isSchool),
    onSuccess: (newQuestion) => {
      queryClient.invalidateQueries({
        queryKey: questionKeys.list(newQuestion.test_id, isSchool),
      });
      toast.success('Вопрос создан');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка создания вопроса: ${error.message}`);
    },
  });
}

export function useUpdateQuestion(isSchool = false) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      testId,
      data,
    }: {
      id: number;
      testId: number;
      data: QuestionUpdate;
    }) => testsApi.updateQuestion(id, data, isSchool).then(() => ({ id, testId })),
    onSuccess: ({ testId }) => {
      queryClient.invalidateQueries({
        queryKey: questionKeys.list(testId, isSchool),
      });
      toast.success('Вопрос обновлен');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка обновления вопроса: ${error.message}`);
    },
  });
}

export function useDeleteQuestion(isSchool = false) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, testId }: { id: number; testId: number }) =>
      testsApi.deleteQuestion(id, isSchool).then(() => ({ id, testId })),
    onSuccess: ({ testId }) => {
      queryClient.invalidateQueries({
        queryKey: questionKeys.list(testId, isSchool),
      });
      toast.success('Вопрос удален');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка удаления вопроса: ${error.message}`);
    },
  });
}
