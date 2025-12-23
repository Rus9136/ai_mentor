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

export const testsApi = {
  // Tests
  getList: async (isSchool = false, chapterId?: number): Promise<Test[]> => {
    const params = chapterId ? `?chapter_id=${chapterId}` : '';
    const { data } = await apiClient.get<Test[]>(
      `${getEndpoint(isSchool)}/tests${params}`
    );
    return data.map(transformTestFromApi);
  },

  getOne: async (id: number, isSchool = false): Promise<Test> => {
    const { data } = await apiClient.get<Test>(
      `${getEndpoint(isSchool)}/tests/${id}`
    );
    return transformTestFromApi(data);
  },

  create: async (payload: TestCreate, isSchool = false): Promise<Test> => {
    const { data } = await apiClient.post<Test>(
      `${getEndpoint(isSchool)}/tests`,
      transformTestForApi(payload)
    );
    return transformTestFromApi(data);
  },

  update: async (
    id: number,
    payload: TestUpdate,
    isSchool = false
  ): Promise<Test> => {
    const { data } = await apiClient.put<Test>(
      `${getEndpoint(isSchool)}/tests/${id}`,
      transformTestForApi(payload)
    );
    return transformTestFromApi(data);
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
