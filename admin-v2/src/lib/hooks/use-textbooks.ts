import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { textbooksApi } from '@/lib/api/textbooks';
import type {
  Textbook,
  TextbookCreate,
  TextbookUpdate,
  Chapter,
  ChapterCreate,
  ChapterUpdate,
  Paragraph,
  ParagraphCreate,
  ParagraphUpdate,
} from '@/types';
import { toast } from 'sonner';

// ==================== Textbooks ====================

export const textbookKeys = {
  all: ['textbooks'] as const,
  lists: () => [...textbookKeys.all, 'list'] as const,
  list: (isSchool: boolean) => [...textbookKeys.lists(), { isSchool }] as const,
  details: () => [...textbookKeys.all, 'detail'] as const,
  detail: (id: number, isSchool: boolean) =>
    [...textbookKeys.details(), id, { isSchool }] as const,
};

export function useTextbooks(isSchool = false) {
  return useQuery({
    queryKey: textbookKeys.list(isSchool),
    queryFn: () => textbooksApi.getList(isSchool),
  });
}

export function useTextbook(id: number, isSchool = false, enabled = true) {
  return useQuery({
    queryKey: textbookKeys.detail(id, isSchool),
    queryFn: () => textbooksApi.getOne(id, isSchool),
    enabled: enabled && id > 0,
  });
}

export function useCreateTextbook(isSchool = false) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TextbookCreate) => textbooksApi.create(data, isSchool),
    onSuccess: (newTextbook) => {
      queryClient.invalidateQueries({ queryKey: textbookKeys.lists() });
      toast.success(`Учебник "${newTextbook.title}" создан`);
    },
    onError: (error: Error) => {
      toast.error(`Ошибка создания: ${error.message}`);
    },
  });
}

export function useUpdateTextbook(isSchool = false) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: TextbookUpdate }) =>
      textbooksApi.update(id, data, isSchool),
    onSuccess: (updatedTextbook) => {
      queryClient.invalidateQueries({ queryKey: textbookKeys.lists() });
      queryClient.invalidateQueries({
        queryKey: textbookKeys.detail(updatedTextbook.id, isSchool),
      });
      toast.success(`Учебник "${updatedTextbook.title}" обновлен`);
    },
    onError: (error: Error) => {
      toast.error(`Ошибка обновления: ${error.message}`);
    },
  });
}

export function useDeleteTextbook(isSchool = false) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => textbooksApi.delete(id, isSchool),
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({ queryKey: textbookKeys.lists() });
      queryClient.removeQueries({
        queryKey: textbookKeys.detail(deletedId, isSchool),
      });
      toast.success('Учебник удален');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка удаления: ${error.message}`);
    },
  });
}

// ==================== Chapters ====================

export const chapterKeys = {
  all: ['chapters'] as const,
  lists: () => [...chapterKeys.all, 'list'] as const,
  list: (textbookId: number, isSchool: boolean) =>
    [...chapterKeys.lists(), { textbookId, isSchool }] as const,
  details: () => [...chapterKeys.all, 'detail'] as const,
  detail: (id: number, isSchool: boolean) =>
    [...chapterKeys.details(), id, { isSchool }] as const,
};

export function useChapters(textbookId: number, isSchool = false, enabled = true) {
  return useQuery({
    queryKey: chapterKeys.list(textbookId, isSchool),
    queryFn: () => textbooksApi.getChapters(textbookId, isSchool),
    enabled: enabled && textbookId > 0,
  });
}

export function useChapter(chapterId: number, isSchool = false, enabled = true) {
  return useQuery({
    queryKey: chapterKeys.detail(chapterId, isSchool),
    queryFn: () => textbooksApi.getChapter(chapterId, isSchool),
    enabled: enabled && chapterId > 0,
  });
}

export function useCreateChapter(isSchool = false) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ChapterCreate) => textbooksApi.createChapter(data, isSchool),
    onSuccess: (newChapter) => {
      queryClient.invalidateQueries({
        queryKey: chapterKeys.list(newChapter.textbook_id, isSchool),
      });
      toast.success(`Глава "${newChapter.title}" создана`);
    },
    onError: (error: Error) => {
      toast.error(`Ошибка создания главы: ${error.message}`);
    },
  });
}

export function useUpdateChapter(isSchool = false) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ChapterUpdate }) =>
      textbooksApi.updateChapter(id, data, isSchool),
    onSuccess: (updatedChapter) => {
      queryClient.invalidateQueries({
        queryKey: chapterKeys.list(updatedChapter.textbook_id, isSchool),
      });
      queryClient.invalidateQueries({
        queryKey: chapterKeys.detail(updatedChapter.id, isSchool),
      });
      toast.success(`Глава "${updatedChapter.title}" обновлена`);
    },
    onError: (error: Error) => {
      toast.error(`Ошибка обновления главы: ${error.message}`);
    },
  });
}

export function useDeleteChapter(isSchool = false) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, textbookId }: { id: number; textbookId: number }) =>
      textbooksApi.deleteChapter(id, isSchool).then(() => ({ id, textbookId })),
    onSuccess: ({ textbookId }) => {
      queryClient.invalidateQueries({
        queryKey: chapterKeys.list(textbookId, isSchool),
      });
      toast.success('Глава удалена');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка удаления главы: ${error.message}`);
    },
  });
}

// ==================== Paragraphs ====================

export const paragraphKeys = {
  all: ['paragraphs'] as const,
  lists: () => [...paragraphKeys.all, 'list'] as const,
  list: (chapterId: number, isSchool: boolean) =>
    [...paragraphKeys.lists(), { chapterId, isSchool }] as const,
  details: () => [...paragraphKeys.all, 'detail'] as const,
  detail: (id: number, isSchool: boolean) =>
    [...paragraphKeys.details(), id, { isSchool }] as const,
};

export function useParagraphs(chapterId: number, isSchool = false, enabled = true) {
  return useQuery({
    queryKey: paragraphKeys.list(chapterId, isSchool),
    queryFn: () => textbooksApi.getParagraphs(chapterId, isSchool),
    enabled: enabled && chapterId > 0,
  });
}

export function useParagraph(paragraphId: number, isSchool = false, enabled = true) {
  return useQuery({
    queryKey: paragraphKeys.detail(paragraphId, isSchool),
    queryFn: () => textbooksApi.getParagraph(paragraphId, isSchool),
    enabled: enabled && paragraphId > 0,
  });
}

export function useCreateParagraph(isSchool = false) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ParagraphCreate) =>
      textbooksApi.createParagraph(data, isSchool),
    onSuccess: (newParagraph) => {
      queryClient.invalidateQueries({
        queryKey: paragraphKeys.list(newParagraph.chapter_id, isSchool),
      });
      toast.success(`Параграф "${newParagraph.title}" создан`);
    },
    onError: (error: Error) => {
      toast.error(`Ошибка создания параграфа: ${error.message}`);
    },
  });
}

export function useUpdateParagraph(isSchool = false) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ParagraphUpdate }) =>
      textbooksApi.updateParagraph(id, data, isSchool),
    onSuccess: (updatedParagraph) => {
      queryClient.invalidateQueries({
        queryKey: paragraphKeys.list(updatedParagraph.chapter_id, isSchool),
      });
      queryClient.invalidateQueries({
        queryKey: paragraphKeys.detail(updatedParagraph.id, isSchool),
      });
      toast.success(`Параграф "${updatedParagraph.title}" обновлен`);
    },
    onError: (error: Error) => {
      toast.error(`Ошибка обновления параграфа: ${error.message}`);
    },
  });
}

export function useDeleteParagraph(isSchool = false) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, chapterId }: { id: number; chapterId: number }) =>
      textbooksApi.deleteParagraph(id, isSchool).then(() => ({ id, chapterId })),
    onSuccess: ({ chapterId }) => {
      queryClient.invalidateQueries({
        queryKey: paragraphKeys.list(chapterId, isSchool),
      });
      toast.success('Параграф удален');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка удаления параграфа: ${error.message}`);
    },
  });
}
