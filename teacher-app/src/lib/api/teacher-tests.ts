import { apiClient } from './client';
import type {
  Test,
  TestCreate,
  TestUpdate,
  Question,
  QuestionCreate,
  QuestionUpdate,
  QuestionOption,
  QuestionOptionCreate,
  QuestionOptionUpdate,
  PaginatedResponse,
} from '@/types/test';

// Transform passing_score: frontend uses 0-100, backend uses 0.0-1.0
const transformTestForApi = <T extends { passing_score?: number }>(data: T): T => {
  if (data.passing_score !== undefined) {
    return { ...data, passing_score: data.passing_score / 100 };
  }
  return data;
};

const transformTestFromApi = <T extends { passing_score: number }>(test: T): T => {
  return { ...test, passing_score: Math.round(test.passing_score * 100) };
};

export const teacherTestsApi = {
  // Tests
  getList: async (params?: { include_global?: boolean; chapter_id?: number; page?: number; page_size?: number }): Promise<PaginatedResponse<Test>> => {
    const { data } = await apiClient.get<PaginatedResponse<Test>>('/teachers/tests', { params });
    return { ...data, items: data.items.map(transformTestFromApi) };
  },

  getOne: async (id: number): Promise<Test> => {
    const { data } = await apiClient.get<Test>(`/teachers/tests/${id}`);
    return transformTestFromApi(data);
  },

  create: async (payload: TestCreate): Promise<Test> => {
    const { data } = await apiClient.post<Test>('/teachers/tests', transformTestForApi(payload));
    return transformTestFromApi(data);
  },

  update: async (id: number, payload: TestUpdate): Promise<Test> => {
    const { data } = await apiClient.put<Test>(`/teachers/tests/${id}`, transformTestForApi(payload));
    return transformTestFromApi(data);
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/teachers/tests/${id}`);
  },

  // Questions
  getQuestions: async (testId: number): Promise<PaginatedResponse<Question>> => {
    const { data } = await apiClient.get<PaginatedResponse<Question>>(`/teachers/tests/${testId}/questions`, {
      params: { page_size: 100 },
    });
    return data;
  },

  createQuestion: async (testId: number, payload: QuestionCreate): Promise<Question> => {
    const { data } = await apiClient.post<Question>(`/teachers/tests/${testId}/questions`, payload);
    return data;
  },

  updateQuestion: async (questionId: number, payload: QuestionUpdate): Promise<Question> => {
    const { data } = await apiClient.put<Question>(`/teachers/tests/questions/${questionId}`, payload);
    return data;
  },

  deleteQuestion: async (questionId: number): Promise<void> => {
    await apiClient.delete(`/teachers/tests/questions/${questionId}`);
  },

  // Options
  createOption: async (questionId: number, payload: QuestionOptionCreate): Promise<QuestionOption> => {
    const { data } = await apiClient.post<QuestionOption>(
      `/teachers/tests/questions/${questionId}/options`,
      payload,
    );
    return data;
  },

  updateOption: async (optionId: number, payload: QuestionOptionUpdate): Promise<QuestionOption> => {
    const { data } = await apiClient.put<QuestionOption>(`/teachers/tests/options/${optionId}`, payload);
    return data;
  },

  deleteOption: async (optionId: number): Promise<void> => {
    await apiClient.delete(`/teachers/tests/options/${optionId}`);
  },
};
