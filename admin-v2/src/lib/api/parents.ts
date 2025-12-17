import { apiClient } from './client';
import type { Parent, ParentCreate, Student } from '@/types';

export const parentsApi = {
  getList: async (): Promise<Parent[]> => {
    const { data } = await apiClient.get<Parent[]>('/admin/school/parents');
    return data;
  },

  getOne: async (id: number): Promise<Parent> => {
    const { data } = await apiClient.get<Parent>(`/admin/school/parents/${id}`);
    return data;
  },

  create: async (payload: ParentCreate): Promise<Parent> => {
    const { data } = await apiClient.post<Parent>('/admin/school/parents', payload);
    return data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/admin/school/parents/${id}`);
  },

  // Children management
  getChildren: async (parentId: number): Promise<Student[]> => {
    const { data } = await apiClient.get<Student[]>(`/admin/school/parents/${parentId}/children`);
    return data;
  },

  addChildren: async (parentId: number, studentIds: number[]): Promise<Parent> => {
    const { data } = await apiClient.post<Parent>(`/admin/school/parents/${parentId}/children`, {
      student_ids: studentIds,
    });
    return data;
  },

  removeChild: async (parentId: number, studentId: number): Promise<Parent> => {
    const { data } = await apiClient.delete<Parent>(
      `/admin/school/parents/${parentId}/children/${studentId}`
    );
    return data;
  },
};
