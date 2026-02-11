import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { embeddedQuestionsApi } from '@/lib/api/embedded-questions';
import type { EmbeddedQuestionCreate, EmbeddedQuestionUpdate } from '@/types';
import { toast } from 'sonner';

export const embeddedQuestionKeys = {
  all: ['embedded-questions'] as const,
  lists: () => [...embeddedQuestionKeys.all, 'list'] as const,
  list: (paragraphId: number, isSchool: boolean) =>
    [...embeddedQuestionKeys.lists(), { paragraphId, isSchool }] as const,
  details: () => [...embeddedQuestionKeys.all, 'detail'] as const,
  detail: (id: number, isSchool: boolean) =>
    [...embeddedQuestionKeys.details(), id, { isSchool }] as const,
};

export function useEmbeddedQuestions(paragraphId: number, isSchool = false, enabled = true) {
  return useQuery({
    queryKey: embeddedQuestionKeys.list(paragraphId, isSchool),
    queryFn: () => embeddedQuestionsApi.getList(paragraphId, isSchool),
    enabled: enabled && paragraphId > 0,
  });
}

export function useCreateEmbeddedQuestion(isSchool = false) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: EmbeddedQuestionCreate) =>
      embeddedQuestionsApi.create(data, isSchool),
    onSuccess: (newQuestion) => {
      queryClient.invalidateQueries({
        queryKey: embeddedQuestionKeys.list(newQuestion.paragraph_id, isSchool),
      });
      toast.success('Вопрос создан');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка создания: ${error.message}`);
    },
  });
}

export function useUpdateEmbeddedQuestion(isSchool = false) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      paragraphId,
      data,
    }: {
      id: number;
      paragraphId: number;
      data: EmbeddedQuestionUpdate;
    }) => embeddedQuestionsApi.update(id, data, isSchool),
    onSuccess: (_, { paragraphId }) => {
      queryClient.invalidateQueries({
        queryKey: embeddedQuestionKeys.list(paragraphId, isSchool),
      });
      toast.success('Вопрос обновлен');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка обновления: ${error.message}`);
    },
  });
}

export function useDeleteEmbeddedQuestion(isSchool = false) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, paragraphId }: { id: number; paragraphId: number }) =>
      embeddedQuestionsApi.delete(id, isSchool),
    onSuccess: (_, { paragraphId }) => {
      queryClient.invalidateQueries({
        queryKey: embeddedQuestionKeys.list(paragraphId, isSchool),
      });
      toast.success('Вопрос удален');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка удаления: ${error.message}`);
    },
  });
}
