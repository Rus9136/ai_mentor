import axios from 'axios';
import { apiClient } from './client';
import type {
  ParagraphContent,
  ParagraphContentUpdate,
  ParagraphContentCardsUpdate,
} from '@/types';

// Direct API URL for file uploads (bypasses Next.js proxy which has body size limits)
const DIRECT_API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.ai-mentor.kz/api/v1';

// Helper to get correct endpoint based on context
const getEndpoint = (isSchool: boolean) =>
  isSchool ? '/admin/school' : '/admin/global';

// Маппинг URL локали на API параметр
// URL использует 'kz', но API принимает 'kk'
const toApiLanguage = (lang: string): string => (lang === 'kz' ? 'kk' : lang);

// Helper to get auth token
const getAuthToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('access_token');
  }
  return null;
};

export const paragraphContentApi = {
  // Get content for a paragraph
  getContent: async (
    paragraphId: number,
    language: string,
    isSchool = false
  ): Promise<ParagraphContent | null> => {
    try {
      const { data } = await apiClient.get<ParagraphContent>(
        `${getEndpoint(isSchool)}/paragraphs/${paragraphId}/content`,
        { params: { language: toApiLanguage(language) } }
      );
      return data;
    } catch (error: unknown) {
      // Return null if content doesn't exist
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { status?: number } };
        if (axiosError.response?.status === 404) {
          return null;
        }
      }
      throw error;
    }
  },

  // Update explain text
  updateContent: async (
    paragraphId: number,
    language: string,
    data: ParagraphContentUpdate,
    isSchool = false
  ): Promise<ParagraphContent> => {
    const { data: result } = await apiClient.put<ParagraphContent>(
      `${getEndpoint(isSchool)}/paragraphs/${paragraphId}/content`,
      data,
      { params: { language: toApiLanguage(language) } }
    );
    return result;
  },

  // Update cards
  updateCards: async (
    paragraphId: number,
    language: string,
    data: ParagraphContentCardsUpdate,
    isSchool = false
  ): Promise<ParagraphContent> => {
    const { data: result } = await apiClient.put<ParagraphContent>(
      `${getEndpoint(isSchool)}/paragraphs/${paragraphId}/content/cards`,
      data,
      { params: { language: toApiLanguage(language) } }
    );
    return result;
  },

  // Upload audio - uses direct API call to bypass Next.js proxy size limits
  uploadAudio: async (
    paragraphId: number,
    language: string,
    file: File,
    isSchool = false
  ): Promise<ParagraphContent> => {
    const formData = new FormData();
    formData.append('file', file);

    const token = getAuthToken();
    const { data } = await axios.post<ParagraphContent>(
      `${DIRECT_API_URL}${getEndpoint(isSchool)}/paragraphs/${paragraphId}/content/audio?language=${toApiLanguage(language)}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      }
    );
    return data;
  },

  // Upload slides - uses direct API call to bypass Next.js proxy size limits
  uploadSlides: async (
    paragraphId: number,
    language: string,
    file: File,
    isSchool = false
  ): Promise<ParagraphContent> => {
    const formData = new FormData();
    formData.append('file', file);

    const token = getAuthToken();
    const { data } = await axios.post<ParagraphContent>(
      `${DIRECT_API_URL}${getEndpoint(isSchool)}/paragraphs/${paragraphId}/content/slides?language=${toApiLanguage(language)}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      }
    );
    return data;
  },

  // Upload video - uses direct API call to bypass Next.js proxy size limits
  uploadVideo: async (
    paragraphId: number,
    language: string,
    file: File,
    isSchool = false
  ): Promise<ParagraphContent> => {
    const formData = new FormData();
    formData.append('file', file);

    const token = getAuthToken();
    const { data } = await axios.post<ParagraphContent>(
      `${DIRECT_API_URL}${getEndpoint(isSchool)}/paragraphs/${paragraphId}/content/video?language=${toApiLanguage(language)}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      }
    );
    return data;
  },

  // Delete audio
  deleteAudio: async (
    paragraphId: number,
    language: string,
    isSchool = false
  ): Promise<void> => {
    await apiClient.delete(
      `${getEndpoint(isSchool)}/paragraphs/${paragraphId}/content/audio`,
      { params: { language: toApiLanguage(language) } }
    );
  },

  // Delete slides
  deleteSlides: async (
    paragraphId: number,
    language: string,
    isSchool = false
  ): Promise<void> => {
    await apiClient.delete(
      `${getEndpoint(isSchool)}/paragraphs/${paragraphId}/content/slides`,
      { params: { language: toApiLanguage(language) } }
    );
  },

  // Delete video
  deleteVideo: async (
    paragraphId: number,
    language: string,
    isSchool = false
  ): Promise<void> => {
    await apiClient.delete(
      `${getEndpoint(isSchool)}/paragraphs/${paragraphId}/content/video`,
      { params: { language: toApiLanguage(language) } }
    );
  },
};
