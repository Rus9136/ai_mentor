import { apiClient } from './client';

export interface DailyQuestAdmin {
  id: number;
  code: string;
  name_kk: string;
  name_ru: string;
  description_kk: string | null;
  description_ru: string | null;
  quest_type: string;
  target_value: number;
  xp_reward: number;
  is_active: boolean;
  school_id: number | null;
  subject_id: number | null;
  textbook_id: number | null;
  paragraph_id: number | null;
  subject_name: string | null;
  textbook_title: string | null;
  paragraph_title: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface DailyQuestCreate {
  code: string;
  name_kk: string;
  name_ru: string;
  description_kk?: string | null;
  description_ru?: string | null;
  quest_type: string;
  target_value: number;
  xp_reward?: number;
  is_active?: boolean;
  subject_id?: number | null;
  textbook_id?: number | null;
  paragraph_id?: number | null;
}

export interface DailyQuestUpdate {
  name_kk?: string;
  name_ru?: string;
  description_kk?: string | null;
  description_ru?: string | null;
  quest_type?: string;
  target_value?: number;
  xp_reward?: number;
  is_active?: boolean;
  subject_id?: number | null;
  textbook_id?: number | null;
  paragraph_id?: number | null;
}

const getEndpoint = (role: string) =>
  role === 'super_admin' ? '/admin/global/daily-quests' : '/admin/school/daily-quests';

export const dailyQuestsApi = {
  getList: async (role: string): Promise<DailyQuestAdmin[]> => {
    const { data } = await apiClient.get<DailyQuestAdmin[]>(getEndpoint(role));
    return data;
  },

  getOne: async (id: number, role: string): Promise<DailyQuestAdmin> => {
    const { data } = await apiClient.get<DailyQuestAdmin>(`${getEndpoint(role)}/${id}`);
    return data;
  },

  create: async (payload: DailyQuestCreate, role: string): Promise<DailyQuestAdmin> => {
    const { data } = await apiClient.post<DailyQuestAdmin>(getEndpoint(role), payload);
    return data;
  },

  update: async (id: number, payload: DailyQuestUpdate, role: string): Promise<DailyQuestAdmin> => {
    const { data } = await apiClient.put<DailyQuestAdmin>(`${getEndpoint(role)}/${id}`, payload);
    return data;
  },

  delete: async (id: number, role: string): Promise<void> => {
    await apiClient.delete(`${getEndpoint(role)}/${id}`);
  },
};
