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
  PaginatedResponse,
} from '@/types';

// Helper to get correct endpoint based on context
const getEndpoint = (isSchool: boolean) =>
  isSchool ? '/admin/school' : '/admin/global';

export const textbooksApi = {
  // Textbooks - both admin/global and admin/school use PaginatedResponse
  getList: async (isSchool = false): Promise<Textbook[]> => {
    const { data } = await apiClient.get<PaginatedResponse<Textbook>>(`${getEndpoint(isSchool)}/textbooks`);
    return data.items;
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

  // Chapters - admin/global uses PaginatedResponse, admin/school uses List
  getChapters: async (textbookId: number, isSchool = false): Promise<Chapter[]> => {
    if (isSchool) {
      const { data } = await apiClient.get<Chapter[]>(
        `${getEndpoint(isSchool)}/textbooks/${textbookId}/chapters`
      );
      return data;
    }
    const { data } = await apiClient.get<PaginatedResponse<Chapter>>(
      `${getEndpoint(isSchool)}/textbooks/${textbookId}/chapters`
    );
    return data.items;
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

  // Paragraphs - admin/global uses PaginatedResponse, admin/school uses List
  getParagraphs: async (chapterId: number, isSchool = false): Promise<Paragraph[]> => {
    if (isSchool) {
      const { data } = await apiClient.get<Paragraph[]>(
        `${getEndpoint(isSchool)}/chapters/${chapterId}/paragraphs`
      );
      return data;
    }
    const { data } = await apiClient.get<PaginatedResponse<Paragraph>>(
      `${getEndpoint(isSchool)}/chapters/${chapterId}/paragraphs`
    );
    return data.items;
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
