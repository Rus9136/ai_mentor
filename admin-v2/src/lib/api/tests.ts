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
} from '@/types';

// Helper to get correct endpoint based on context
const getEndpoint = (isSchool: boolean) =>
  isSchool ? '/admin/school' : '/admin/global';

export const testsApi = {
  // Tests
  getList: async (isSchool = false, chapterId?: number): Promise<Test[]> => {
    const params = chapterId ? `?chapter_id=${chapterId}` : '';
    const { data } = await apiClient.get<Test[]>(
      `${getEndpoint(isSchool)}/tests${params}`
    );
    return data;
  },

  getOne: async (id: number, isSchool = false): Promise<Test> => {
    const { data } = await apiClient.get<Test>(
      `${getEndpoint(isSchool)}/tests/${id}`
    );
    return data;
  },

  create: async (payload: TestCreate, isSchool = false): Promise<Test> => {
    const { data } = await apiClient.post<Test>(
      `${getEndpoint(isSchool)}/tests`,
      payload
    );
    return data;
  },

  update: async (
    id: number,
    payload: TestUpdate,
    isSchool = false
  ): Promise<Test> => {
    const { data } = await apiClient.put<Test>(
      `${getEndpoint(isSchool)}/tests/${id}`,
      payload
    );
    return data;
  },

  delete: async (id: number, isSchool = false): Promise<void> => {
    await apiClient.delete(`${getEndpoint(isSchool)}/tests/${id}`);
  },

  // Questions
  getQuestions: async (testId: number, isSchool = false): Promise<Question[]> => {
    const { data } = await apiClient.get<Question[]>(
      `${getEndpoint(isSchool)}/tests/${testId}/questions`
    );
    return data;
  },

  getQuestion: async (questionId: number, isSchool = false): Promise<Question> => {
    const { data } = await apiClient.get<Question>(
      `${getEndpoint(isSchool)}/questions/${questionId}`
    );
    return data;
  },

  createQuestion: async (
    testId: number,
    payload: QuestionCreate,
    isSchool = false
  ): Promise<Question> => {
    const { data } = await apiClient.post<Question>(
      `${getEndpoint(isSchool)}/tests/${testId}/questions`,
      payload
    );
    return data;
  },

  updateQuestion: async (
    questionId: number,
    payload: QuestionUpdate,
    isSchool = false
  ): Promise<Question> => {
    const { data } = await apiClient.put<Question>(
      `${getEndpoint(isSchool)}/questions/${questionId}`,
      payload
    );
    return data;
  },

  deleteQuestion: async (questionId: number, isSchool = false): Promise<void> => {
    await apiClient.delete(`${getEndpoint(isSchool)}/questions/${questionId}`);
  },

  // Question Options
  createOption: async (
    questionId: number,
    payload: QuestionOptionCreate,
    isSchool = false
  ): Promise<QuestionOption> => {
    const { data } = await apiClient.post<QuestionOption>(
      `${getEndpoint(isSchool)}/questions/${questionId}/options`,
      payload
    );
    return data;
  },

  updateOption: async (
    optionId: number,
    payload: QuestionOptionUpdate,
    isSchool = false
  ): Promise<QuestionOption> => {
    const { data } = await apiClient.put<QuestionOption>(
      `${getEndpoint(isSchool)}/options/${optionId}`,
      payload
    );
    return data;
  },

  deleteOption: async (optionId: number, isSchool = false): Promise<void> => {
    await apiClient.delete(`${getEndpoint(isSchool)}/options/${optionId}`);
  },
};
