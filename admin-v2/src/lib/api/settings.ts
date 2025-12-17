import { apiClient } from './client';
import type { School, SchoolUpdate } from '@/types';

export const settingsApi = {
  getSchool: async (): Promise<School> => {
    const { data } = await apiClient.get<School>('/admin/school/settings');
    return data;
  },

  updateSchool: async (payload: SchoolUpdate): Promise<School> => {
    const { data } = await apiClient.put<School>('/admin/school/settings', payload);
    return data;
  },
};
