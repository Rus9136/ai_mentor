import { apiClient } from './client';
import type { School, SchoolCreate, SchoolUpdate } from '@/types';

export const schoolsApi = {
  getList: async (): Promise<School[]> => {
    const { data } = await apiClient.get<School[]>('/admin/schools');
    return data;
  },

  getOne: async (id: number): Promise<School> => {
    const { data } = await apiClient.get<School>(`/admin/schools/${id}`);
    return data;
  },

  create: async (payload: SchoolCreate): Promise<School> => {
    const { data } = await apiClient.post<School>('/admin/schools', payload);
    return data;
  },

  update: async (id: number, payload: SchoolUpdate): Promise<School> => {
    const { data } = await apiClient.put<School>(`/admin/schools/${id}`, payload);
    return data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/admin/schools/${id}`);
  },

  block: async (id: number): Promise<School> => {
    const { data } = await apiClient.patch<School>(`/admin/schools/${id}/block`);
    return data;
  },

  unblock: async (id: number): Promise<School> => {
    const { data } = await apiClient.patch<School>(`/admin/schools/${id}/unblock`);
    return data;
  },
};
