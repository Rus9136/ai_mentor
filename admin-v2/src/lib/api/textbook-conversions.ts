import axios from 'axios';
import type { TextbookConversion, ConversionUploadResponse } from '@/types';

const DIRECT_API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.ai-mentor.kz/api/v1';

const getAuthToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('access_token');
  }
  return null;
};

export const textbookConversionsApi = {
  uploadPdf: async (textbookId: number, file: File): Promise<ConversionUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const token = getAuthToken();
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
      const token = getAuthToken();
      const { data } = await axios.get<TextbookConversion>(
        `${DIRECT_API_URL}/admin/global/textbooks/${textbookId}/conversions/status`,
        {
          headers: {
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
        }
      );
      return data;
    } catch (error: unknown) {
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { status?: number } };
        if (axiosError.response?.status === 404) {
          return null;
        }
      }
      throw error;
    }
  },

  downloadMmd: (textbookId: number): string => {
    const token = getAuthToken();
    return `${DIRECT_API_URL}/admin/global/textbooks/${textbookId}/conversions/mmd?token=${token}`;
  },
};
