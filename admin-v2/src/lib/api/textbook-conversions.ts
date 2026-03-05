import axios from 'axios';
import { apiClient } from './client';
import type { TextbookConversion, ConversionUploadResponse } from '@/types';

const DIRECT_API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.ai-mentor.kz/api/v1';

export const textbookConversionsApi = {
  uploadPdf: async (textbookId: number, file: File): Promise<ConversionUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    // Upload directly to backend (bypass Next.js proxy which has 10MB body limit)
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    const { data } = await axios.post<ConversionUploadResponse>(
      `${DIRECT_API_URL}/admin/global/textbooks/${textbookId}/conversions`,
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

  getStatus: async (textbookId: number): Promise<TextbookConversion | null> => {
    try {
      const { data } = await apiClient.get<TextbookConversion>(
        `/admin/global/textbooks/${textbookId}/conversions/status`,
      );
      return data;
    } catch (error: unknown) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  downloadMmd: (textbookId: number): string => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    return `${DIRECT_API_URL}/admin/global/textbooks/${textbookId}/conversions/mmd?token=${token}`;
  },
};
