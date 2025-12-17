import { apiClient } from './client';
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

// Helper to get correct endpoint based on context
const getEndpoint = (isSchool: boolean) =>
  isSchool ? '/admin/school' : '/admin/global';

export const textbooksApi = {
  // Textbooks
  getList: async (isSchool = false): Promise<Textbook[]> => {
    const { data } = await apiClient.get<Textbook[]>(`${getEndpoint(isSchool)}/textbooks`);
    return data;
  },

  getOne: async (id: number, isSchool = false): Promise<Textbook> => {
    const { data } = await apiClient.get<Textbook>(`${getEndpoint(isSchool)}/textbooks/${id}`);
    return data;
  },

  create: async (payload: TextbookCreate, isSchool = false): Promise<Textbook> => {
    const { data } = await apiClient.post<Textbook>(`${getEndpoint(isSchool)}/textbooks`, payload);
    return data;
  },

  update: async (id: number, payload: TextbookUpdate, isSchool = false): Promise<Textbook> => {
    const { data } = await apiClient.put<Textbook>(`${getEndpoint(isSchool)}/textbooks/${id}`, payload);
    return data;
  },

  delete: async (id: number, isSchool = false): Promise<void> => {
    await apiClient.delete(`${getEndpoint(isSchool)}/textbooks/${id}`);
  },

  // Customize (fork) global textbook for school
  customize: async (globalTextbookId: number): Promise<Textbook> => {
    const { data } = await apiClient.post<Textbook>(
      `/admin/school/textbooks/${globalTextbookId}/customize`
    );
    return data;
  },

  // Chapters
  getChapters: async (textbookId: number, isSchool = false): Promise<Chapter[]> => {
    const { data } = await apiClient.get<Chapter[]>(
      `${getEndpoint(isSchool)}/textbooks/${textbookId}/chapters`
    );
    return data;
  },

  getChapter: async (chapterId: number, isSchool = false): Promise<Chapter> => {
    const { data } = await apiClient.get<Chapter>(
      `${getEndpoint(isSchool)}/chapters/${chapterId}`
    );
    return data;
  },

  createChapter: async (payload: ChapterCreate, isSchool = false): Promise<Chapter> => {
    const { data } = await apiClient.post<Chapter>(`${getEndpoint(isSchool)}/chapters`, payload);
    return data;
  },

  updateChapter: async (
    chapterId: number,
    payload: ChapterUpdate,
    isSchool = false
  ): Promise<Chapter> => {
    const { data } = await apiClient.put<Chapter>(
      `${getEndpoint(isSchool)}/chapters/${chapterId}`,
      payload
    );
    return data;
  },

  deleteChapter: async (chapterId: number, isSchool = false): Promise<void> => {
    await apiClient.delete(`${getEndpoint(isSchool)}/chapters/${chapterId}`);
  },

  // Paragraphs
  getParagraphs: async (chapterId: number, isSchool = false): Promise<Paragraph[]> => {
    const { data } = await apiClient.get<Paragraph[]>(
      `${getEndpoint(isSchool)}/chapters/${chapterId}/paragraphs`
    );
    return data;
  },

  getParagraph: async (paragraphId: number, isSchool = false): Promise<Paragraph> => {
    const { data } = await apiClient.get<Paragraph>(
      `${getEndpoint(isSchool)}/paragraphs/${paragraphId}`
    );
    return data;
  },

  createParagraph: async (payload: ParagraphCreate, isSchool = false): Promise<Paragraph> => {
    const { data } = await apiClient.post<Paragraph>(
      `${getEndpoint(isSchool)}/paragraphs`,
      payload
    );
    return data;
  },

  updateParagraph: async (
    paragraphId: number,
    payload: ParagraphUpdate,
    isSchool = false
  ): Promise<Paragraph> => {
    const { data } = await apiClient.put<Paragraph>(
      `${getEndpoint(isSchool)}/paragraphs/${paragraphId}`,
      payload
    );
    return data;
  },

  deleteParagraph: async (paragraphId: number, isSchool = false): Promise<void> => {
    await apiClient.delete(`${getEndpoint(isSchool)}/paragraphs/${paragraphId}`);
  },
};
