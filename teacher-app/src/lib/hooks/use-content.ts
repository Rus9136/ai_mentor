/**
 * React Query hooks for teacher content browsing.
 * Used by ContentSelector in homework creation.
 */

import { useQuery } from '@tanstack/react-query';
import { getTextbooks, getChapters, getParagraphs } from '@/lib/api/content';

// Query key factory for content
export const contentKeys = {
  all: ['content'] as const,
  textbooks: () => [...contentKeys.all, 'textbooks'] as const,
  chapters: (textbookId: number) => [...contentKeys.all, 'chapters', textbookId] as const,
  paragraphs: (chapterId: number) => [...contentKeys.all, 'paragraphs', chapterId] as const,
};

/**
 * Hook to get list of textbooks available to the teacher.
 */
export function useTextbooks() {
  return useQuery({
    queryKey: contentKeys.textbooks(),
    queryFn: getTextbooks,
  });
}

/**
 * Hook to get chapters for a textbook.
 * @param textbookId - Textbook ID (query is disabled when 0 or falsy)
 */
export function useChapters(textbookId: number) {
  return useQuery({
    queryKey: contentKeys.chapters(textbookId),
    queryFn: () => getChapters(textbookId),
    enabled: !!textbookId && textbookId > 0,
  });
}

/**
 * Hook to get paragraphs for a chapter.
 * @param chapterId - Chapter ID (query is disabled when 0 or falsy)
 */
export function useParagraphs(chapterId: number) {
  return useQuery({
    queryKey: contentKeys.paragraphs(chapterId),
    queryFn: () => getParagraphs(chapterId),
    enabled: !!chapterId && chapterId > 0,
  });
}
