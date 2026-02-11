import { apiClient } from './client';
import type {
  EmbeddedQuestion,
  EmbeddedQuestionCreate,
  EmbeddedQuestionUpdate,
} from '@/types';

const getEndpoint = (isSchool: boolean) =>
  isSchool ? '/admin/school' : '/admin/global';

export const embeddedQuestionsApi = {
  getList: async (paragraphId: number, isSchool = false): Promise<EmbeddedQuestion[]> => {
    const { data } = await apiClient.get<EmbeddedQuestion[]>(
      `${getEndpoint(isSchool)}/paragraphs/${paragraphId}/embedded-questions`
    );
    return data;
  },

  getOne: async (id: number, isSchool = false): Promise<EmbeddedQuestion> => {
    const { data } = await apiClient.get<EmbeddedQuestion>(
      `${getEndpoint(isSchool)}/embedded-questions/${id}`
    );
    return data;
  },

  create: async (payload: EmbeddedQuestionCreate, isSchool = false): Promise<EmbeddedQuestion> => {
    const { data } = await apiClient.post<EmbeddedQuestion>(
      `${getEndpoint(isSchool)}/paragraphs/${payload.paragraph_id}/embedded-questions`,
      payload
    );
    return data;
  },

  update: async (id: number, payload: EmbeddedQuestionUpdate, isSchool = false): Promise<EmbeddedQuestion> => {
    const { data } = await apiClient.put<EmbeddedQuestion>(
      `${getEndpoint(isSchool)}/embedded-questions/${id}`,
      payload
    );
    return data;
  },

  delete: async (id: number, isSchool = false): Promise<void> => {
    await apiClient.delete(`${getEndpoint(isSchool)}/embedded-questions/${id}`);
  },
};
