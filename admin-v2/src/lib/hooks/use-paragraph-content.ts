import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { paragraphContentApi } from '@/lib/api/paragraph-content';
import type {
  ParagraphContent,
  ParagraphContentUpdate,
  ParagraphContentCardsUpdate,
  CardItem,
} from '@/types';
import { toast } from 'sonner';

// Query Keys Factory
export const paragraphContentKeys = {
  all: ['paragraph-content'] as const,
  details: () => [...paragraphContentKeys.all, 'detail'] as const,
  detail: (paragraphId: number, language: string, isSchool: boolean) =>
    [...paragraphContentKeys.details(), { paragraphId, language, isSchool }] as const,
};

// ==================== Queries ====================

export function useParagraphContent(
  paragraphId: number,
  language: string,
  isSchool = false,
  enabled = true
) {
  return useQuery({
    queryKey: paragraphContentKeys.detail(paragraphId, language, isSchool),
    queryFn: () => paragraphContentApi.getContent(paragraphId, language, isSchool),
    enabled: enabled && paragraphId > 0,
    // Don't keep previous data when language changes - show loading state instead
    placeholderData: undefined,
    // Refetch when query key changes (language switch)
    refetchOnMount: true,
    staleTime: 0,
  });
}

// ==================== Mutations ====================

export function useUpdateParagraphContent(isSchool = false) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      paragraphId,
      language,
      data,
    }: {
      paragraphId: number;
      language: string;
      data: ParagraphContentUpdate;
    }) => paragraphContentApi.updateContent(paragraphId, language, data, isSchool),
    onSuccess: (updatedContent, { paragraphId, language }) => {
      queryClient.setQueryData(
        paragraphContentKeys.detail(paragraphId, language, isSchool),
        updatedContent
      );
      toast.success('Текст объяснения сохранен');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка сохранения: ${error.message}`);
    },
  });
}

export function useUpdateParagraphCards(isSchool = false) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      paragraphId,
      language,
      cards,
    }: {
      paragraphId: number;
      language: string;
      cards: CardItem[];
    }) => paragraphContentApi.updateCards(paragraphId, language, { cards }, isSchool),
    onSuccess: (updatedContent, { paragraphId, language }) => {
      queryClient.setQueryData(
        paragraphContentKeys.detail(paragraphId, language, isSchool),
        updatedContent
      );
      toast.success('Карточки сохранены');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка сохранения карточек: ${error.message}`);
    },
  });
}

export function useUploadAudio(isSchool = false) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      paragraphId,
      language,
      file,
    }: {
      paragraphId: number;
      language: string;
      file: File;
    }) => paragraphContentApi.uploadAudio(paragraphId, language, file, isSchool),
    onSuccess: (_, { paragraphId, language }) => {
      // Invalidate to refetch full content (backend returns partial response)
      queryClient.invalidateQueries({
        queryKey: paragraphContentKeys.detail(paragraphId, language, isSchool),
      });
      toast.success('Аудио загружено');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка загрузки аудио: ${error.message}`);
    },
  });
}

export function useUploadSlides(isSchool = false) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      paragraphId,
      language,
      file,
    }: {
      paragraphId: number;
      language: string;
      file: File;
    }) => paragraphContentApi.uploadSlides(paragraphId, language, file, isSchool),
    onSuccess: (_, { paragraphId, language }) => {
      // Invalidate to refetch full content (backend returns partial response)
      queryClient.invalidateQueries({
        queryKey: paragraphContentKeys.detail(paragraphId, language, isSchool),
      });
      toast.success('Слайды загружены');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка загрузки слайдов: ${error.message}`);
    },
  });
}

export function useUploadVideo(isSchool = false) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      paragraphId,
      language,
      file,
    }: {
      paragraphId: number;
      language: string;
      file: File;
    }) => paragraphContentApi.uploadVideo(paragraphId, language, file, isSchool),
    onSuccess: (_, { paragraphId, language }) => {
      // Invalidate to refetch full content (backend returns partial response)
      queryClient.invalidateQueries({
        queryKey: paragraphContentKeys.detail(paragraphId, language, isSchool),
      });
      toast.success('Видео загружено');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка загрузки видео: ${error.message}`);
    },
  });
}

export function useDeleteAudio(isSchool = false) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      paragraphId,
      language,
    }: {
      paragraphId: number;
      language: string;
    }) => paragraphContentApi.deleteAudio(paragraphId, language, isSchool),
    onSuccess: (_, { paragraphId, language }) => {
      queryClient.invalidateQueries({
        queryKey: paragraphContentKeys.detail(paragraphId, language, isSchool),
      });
      toast.success('Аудио удалено');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка удаления аудио: ${error.message}`);
    },
  });
}

export function useDeleteSlides(isSchool = false) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      paragraphId,
      language,
    }: {
      paragraphId: number;
      language: string;
    }) => paragraphContentApi.deleteSlides(paragraphId, language, isSchool),
    onSuccess: (_, { paragraphId, language }) => {
      queryClient.invalidateQueries({
        queryKey: paragraphContentKeys.detail(paragraphId, language, isSchool),
      });
      toast.success('Слайды удалены');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка удаления слайдов: ${error.message}`);
    },
  });
}

export function useDeleteVideo(isSchool = false) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      paragraphId,
      language,
    }: {
      paragraphId: number;
      language: string;
    }) => paragraphContentApi.deleteVideo(paragraphId, language, isSchool),
    onSuccess: (_, { paragraphId, language }) => {
      queryClient.invalidateQueries({
        queryKey: paragraphContentKeys.detail(paragraphId, language, isSchool),
      });
      toast.success('Видео удалено');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка удаления видео: ${error.message}`);
    },
  });
}
