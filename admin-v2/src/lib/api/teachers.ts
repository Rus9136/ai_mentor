import { apiClient } from './client';
import type { Teacher, TeacherCreate, TeacherUpdate } from '@/types';

export const teachersApi = {
  getList: async (): Promise<Teacher[]> => {
    const { data } = await apiClient.get<Teacher[]>('/admin/school/teachers');
    return data;
  },

  getOne: async (id: number): Promise<Teacher> => {
    const { data } = await apiClient.get<Teacher>(`/admin/school/teachers/${id}`);
    return data;
  },

  create: async (payload: TeacherCreate): Promise<Teacher> => {
    const { data } = await apiClient.post<Teacher>('/admin/school/teachers', payload);
    return data;
  },

  update: async (id: number, payload: TeacherUpdate): Promise<Teacher> => {
    const { data } = await apiClient.put<Teacher>(`/admin/school/teachers/${id}`, payload);
    return data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/admin/school/teachers/${id}`);
  },
};
