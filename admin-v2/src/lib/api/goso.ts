import { apiClient } from './client';
import type {
  Subject,
  Framework,
  GosoSection,
  LearningOutcome,
} from '@/types';

export const gosoApi = {
  // Subjects
  getSubjects: async (): Promise<Subject[]> => {
    const { data } = await apiClient.get<Subject[]>('/goso/subjects');
    return data;
  },

  getSubject: async (id: number): Promise<Subject> => {
    const { data } = await apiClient.get<Subject>(`/goso/subjects/${id}`);
    return data;
  },

  // Frameworks
  getFrameworks: async (subjectId?: number): Promise<Framework[]> => {
    const params = subjectId ? `?subject_id=${subjectId}` : '';
    const { data } = await apiClient.get<Framework[]>(`/goso/frameworks${params}`);
    return data;
  },

  getFramework: async (id: number): Promise<Framework> => {
    const { data } = await apiClient.get<Framework>(`/goso/frameworks/${id}`);
    return data;
  },

  // Sections
  getSections: async (frameworkId: number): Promise<GosoSection[]> => {
    const { data } = await apiClient.get<GosoSection[]>(
      `/goso/frameworks/${frameworkId}/sections`
    );
    return data;
  },

  // Learning Outcomes
  getOutcomes: async (params?: {
    framework_id?: number;
    subsection_id?: number;
    grade?: number;
    search?: string;
  }): Promise<LearningOutcome[]> => {
    const searchParams = new URLSearchParams();
    if (params?.framework_id) searchParams.set('framework_id', String(params.framework_id));
    if (params?.subsection_id) searchParams.set('subsection_id', String(params.subsection_id));
    if (params?.grade) searchParams.set('grade', String(params.grade));
    if (params?.search) searchParams.set('search', params.search);

    const queryString = searchParams.toString();
    const url = queryString ? `/goso/outcomes?${queryString}` : '/goso/outcomes';

    const { data } = await apiClient.get<LearningOutcome[]>(url);
    return data;
  },

  getOutcome: async (id: number): Promise<LearningOutcome> => {
    const { data } = await apiClient.get<LearningOutcome>(`/goso/outcomes/${id}`);
    return data;
  },
};
