import { apiClient } from './client';
import type { PaginatedResponse } from '@/types';

export interface GlobalUser {
  id: number;
  email: string;
  role: string;
  school_id: number | null;
  school_name: string | null;
  first_name: string;
  last_name: string;
  middle_name: string | null;
  phone: string | null;
  is_active: boolean;
  is_verified: boolean;
  auth_provider: string | null;
  created_at: string;
}

export interface UsersListParams {
  page?: number;
  page_size?: number;
  role?: string;
  is_active?: boolean;
  search?: string;
}

export const globalUsersApi = {
  getList: async (params?: UsersListParams): Promise<PaginatedResponse<GlobalUser>> => {
    const { data } = await apiClient.get<PaginatedResponse<GlobalUser>>(
      '/admin/global/users',
      { params }
    );
    return data;
  },
};
