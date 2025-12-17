import { apiClient } from './client';
import type { Student, StudentCreate, StudentUpdate } from '@/types';

export const studentsApi = {
  getList: async (): Promise<Student[]> => {
    const { data } = await apiClient.get<Student[]>('/admin/school/students');
    return data;
  },

  getOne: async (id: number): Promise<Student> => {
    const { data } = await apiClient.get<Student>(`/admin/school/students/${id}`);
    return data;
  },

  create: async (payload: StudentCreate): Promise<Student> => {
    const { data } = await apiClient.post<Student>('/admin/school/students', payload);
    return data;
  },

  update: async (id: number, payload: StudentUpdate): Promise<Student> => {
    const { data } = await apiClient.put<Student>(`/admin/school/students/${id}`, payload);
    return data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/admin/school/students/${id}`);
  },
};
