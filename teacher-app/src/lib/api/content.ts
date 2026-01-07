/**
 * API functions for teacher content browsing.
 * Used by ContentSelector in homework creation.
 */

import { apiClient } from './client';
import type { TextbookListItem, ChapterListItem, ParagraphListItem } from '@/types/content';

// Pagination response type
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/**
 * Get list of textbooks available to the teacher (global + school-specific).
 */
export async function getTextbooks(): Promise<TextbookListItem[]> {
  const response = await apiClient.get<PaginatedResponse<TextbookListItem>>('/teachers/textbooks');
  return response.data.items;
}

/**
 * Get list of chapters in a textbook.
 */
export async function getChapters(textbookId: number): Promise<ChapterListItem[]> {
  const response = await apiClient.get<PaginatedResponse<ChapterListItem>>(`/teachers/textbooks/${textbookId}/chapters`);
  return response.data.items;
}

/**
 * Get list of paragraphs in a chapter.
 */
export async function getParagraphs(chapterId: number): Promise<ParagraphListItem[]> {
  const response = await apiClient.get<PaginatedResponse<ParagraphListItem>>(`/teachers/chapters/${chapterId}/paragraphs`);
  return response.data.items;
}
