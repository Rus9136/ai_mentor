import { apiClient } from './client';
import type { Test, TestCreate, TestUpdate, Question, QuestionCreate, QuestionUpdate, QuestionOption, QuestionOptionCreate, QuestionOptionUpdate } from '@/types';

export const schoolTestsApi = {
  getList: async (): Promise<Test[]> => {
    const { data } = await apiClient.get<Test[]>('/admin/school/tests');
    return data;
  },

  getOne: async (id: number): Promise<Test> => {
    const { data } = await apiClient.get<Test>(`/admin/school/tests/${id}`);
    return data;
  },

  create: async (payload: TestCreate): Promise<Test> => {
    const { data } = await apiClient.post<Test>('/admin/school/tests', payload);
    return data;
  },

  update: async (id: number, payload: TestUpdate): Promise<Test> => {
    const { data } = await apiClient.put<Test>(`/admin/school/tests/${id}`, payload);
    return data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/admin/school/tests/${id}`);
  },

  // Questions
  getQuestions: async (testId: number): Promise<Question[]> => {
    const { data } = await apiClient.get<Question[]>(`/admin/school/tests/${testId}/questions`);
    return data;
  },

  createQuestion: async (testId: number, payload: QuestionCreate): Promise<Question> => {
    const { data } = await apiClient.post<Question>(
      `/admin/school/tests/${testId}/questions`,
      payload
    );
    return data;
  },

  updateQuestion: async (questionId: number, payload: QuestionUpdate): Promise<Question> => {
    const { data } = await apiClient.put<Question>(
      `/admin/school/questions/${questionId}`,
      payload
    );
    return data;
  },

  deleteQuestion: async (questionId: number): Promise<void> => {
    await apiClient.delete(`/admin/school/questions/${questionId}`);
  },

  // Options
  createOption: async (questionId: number, payload: QuestionOptionCreate): Promise<QuestionOption> => {
    const { data } = await apiClient.post<QuestionOption>(
      `/admin/school/questions/${questionId}/options`,
      payload
    );
    return data;
  },

  updateOption: async (optionId: number, payload: QuestionOptionUpdate): Promise<QuestionOption> => {
    const { data } = await apiClient.put<QuestionOption>(
      `/admin/school/options/${optionId}`,
      payload
    );
    return data;
  },

  deleteOption: async (optionId: number): Promise<void> => {
    await apiClient.delete(`/admin/school/options/${optionId}`);
  },
};
