import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { schoolTextbooksApi } from '@/lib/api/school-textbooks';
import type { Textbook, TextbookCreate, TextbookUpdate } from '@/types';
import { toast } from 'sonner';

// Query keys factory
export const schoolTextbookKeys = {
  all: ['school-textbooks'] as const,
  lists: () => [...schoolTextbookKeys.all, 'list'] as const,
  list: (filters?: Record<string, unknown>) => [...schoolTextbookKeys.lists(), filters] as const,
  details: () => [...schoolTextbookKeys.all, 'detail'] as const,
  detail: (id: number) => [...schoolTextbookKeys.details(), id] as const,
  chapters: (textbookId: number) => [...schoolTextbookKeys.detail(textbookId), 'chapters'] as const,
  paragraphs: (chapterId: number) => ['school-paragraphs', chapterId] as const,
};

// Get all textbooks (global + school)
export function useSchoolTextbooks(includeGlobal = true) {
  return useQuery({
    queryKey: schoolTextbookKeys.list({ includeGlobal }),
    queryFn: () => schoolTextbooksApi.getList(includeGlobal),
  });
}

// Get single textbook by ID
export function useSchoolTextbook(id: number, enabled = true) {
  return useQuery({
    queryKey: schoolTextbookKeys.detail(id),
    queryFn: () => schoolTextbooksApi.getOne(id),
    enabled: enabled && id > 0,
  });
}

// Create textbook mutation
export function useCreateSchoolTextbook() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TextbookCreate) => schoolTextbooksApi.create(data),
    onSuccess: (newTextbook) => {
      queryClient.invalidateQueries({ queryKey: schoolTextbookKeys.lists() });
      toast.success(`Учебник "${newTextbook.title}" создан`);
    },
    onError: (error: Error) => {
      toast.error(`Ошибка создания: ${error.message}`);
    },
  });
}

// Update textbook mutation
export function useUpdateSchoolTextbook() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: TextbookUpdate }) =>
      schoolTextbooksApi.update(id, data),
    onSuccess: (updatedTextbook) => {
      queryClient.invalidateQueries({ queryKey: schoolTextbookKeys.lists() });
      queryClient.invalidateQueries({
        queryKey: schoolTextbookKeys.detail(updatedTextbook.id),
      });
      toast.success(`Учебник "${updatedTextbook.title}" обновлен`);
    },
    onError: (error: Error) => {
      toast.error(`Ошибка обновления: ${error.message}`);
    },
  });
}

// Delete textbook mutation
export function useDeleteSchoolTextbook() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => schoolTextbooksApi.delete(id),
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({ queryKey: schoolTextbookKeys.lists() });
      queryClient.removeQueries({ queryKey: schoolTextbookKeys.detail(deletedId) });
      toast.success('Учебник удален');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка удаления: ${error.message}`);
    },
  });
}

// Customize (fork) global textbook
export function useCustomizeTextbook() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (globalTextbookId: number) => schoolTextbooksApi.customize(globalTextbookId),
    onSuccess: (newTextbook) => {
      queryClient.invalidateQueries({ queryKey: schoolTextbookKeys.lists() });
      toast.success(`Учебник "${newTextbook.title}" скопирован в вашу школу`);
    },
    onError: (error: Error) => {
      toast.error(`Ошибка кастомизации: ${error.message}`);
    },
  });
}

// Get chapters for textbook
export function useSchoolTextbookChapters(textbookId: number, enabled = true) {
  return useQuery({
    queryKey: schoolTextbookKeys.chapters(textbookId),
    queryFn: () => schoolTextbooksApi.getChapters(textbookId),
    enabled: enabled && textbookId > 0,
  });
}

// Get paragraphs for chapter
export function useSchoolChapterParagraphs(chapterId: number, enabled = true) {
  return useQuery({
    queryKey: schoolTextbookKeys.paragraphs(chapterId),
    queryFn: () => schoolTextbooksApi.getParagraphs(chapterId),
    enabled: enabled && chapterId > 0,
  });
}
