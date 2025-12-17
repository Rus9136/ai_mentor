import { apiClient } from './client';
import type { Textbook, TextbookCreate, TextbookUpdate, Chapter, Paragraph } from '@/types';

export const schoolTextbooksApi = {
  // Get both global and school textbooks
  getList: async (includeGlobal = true): Promise<Textbook[]> => {
    const { data } = await apiClient.get<Textbook[]>('/admin/school/textbooks', {
      params: { include_global: includeGlobal },
    });
    return data;
  },

  getOne: async (id: number): Promise<Textbook> => {
    const { data } = await apiClient.get<Textbook>(`/admin/school/textbooks/${id}`);
    return data;
  },

  create: async (payload: TextbookCreate): Promise<Textbook> => {
    const { data } = await apiClient.post<Textbook>('/admin/school/textbooks', payload);
    return data;
  },

  update: async (id: number, payload: TextbookUpdate): Promise<Textbook> => {
    const { data } = await apiClient.put<Textbook>(`/admin/school/textbooks/${id}`, payload);
    return data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/admin/school/textbooks/${id}`);
  },

  // Fork/customize a global textbook
  customize: async (globalTextbookId: number): Promise<Textbook> => {
    const { data } = await apiClient.post<Textbook>(
      `/admin/school/textbooks/${globalTextbookId}/customize`
    );
    return data;
  },

  // Chapters
  getChapters: async (textbookId: number): Promise<Chapter[]> => {
    const { data } = await apiClient.get<Chapter[]>(
      `/admin/school/textbooks/${textbookId}/chapters`
    );
    return data;
  },

  createChapter: async (payload: { textbook_id: number; title: string; number: number; order: number; description?: string }): Promise<Chapter> => {
    const { data } = await apiClient.post<Chapter>('/admin/school/chapters', payload);
    return data;
  },

  updateChapter: async (id: number, payload: Partial<Chapter>): Promise<Chapter> => {
    const { data } = await apiClient.put<Chapter>(`/admin/school/chapters/${id}`, payload);
    return data;
  },

  deleteChapter: async (id: number): Promise<void> => {
    await apiClient.delete(`/admin/school/chapters/${id}`);
  },

  // Paragraphs
  getParagraphs: async (chapterId: number): Promise<Paragraph[]> => {
    const { data } = await apiClient.get<Paragraph[]>(
      `/admin/school/chapters/${chapterId}/paragraphs`
    );
    return data;
  },

  createParagraph: async (payload: { chapter_id: number; title: string; number: number; order: number; content: string }): Promise<Paragraph> => {
    const { data } = await apiClient.post<Paragraph>('/admin/school/paragraphs', payload);
    return data;
  },

  updateParagraph: async (id: number, payload: Partial<Paragraph>): Promise<Paragraph> => {
    const { data } = await apiClient.put<Paragraph>(`/admin/school/paragraphs/${id}`, payload);
    return data;
  },

  deleteParagraph: async (id: number): Promise<void> => {
    await apiClient.delete(`/admin/school/paragraphs/${id}`);
  },
};
