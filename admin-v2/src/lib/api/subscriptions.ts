import { apiClient } from './client';

export interface SubscriptionPlan {
  id: number;
  name: string;
  display_name: string;
  daily_message_limit: number | null;
  feature_limits: Record<string, number>;
  is_active: boolean;
  sort_order: number;
  description: string | null;
  price_monthly_kzt: number | null;
  price_yearly_kzt: number | null;
  created_at: string;
  updated_at: string;
}

export interface SchoolSubscription {
  id: number;
  school_id: number;
  plan_id: number;
  plan: SubscriptionPlan | null;
  starts_at: string;
  expires_at: string | null;
  limit_overrides: Record<string, number> | null;
  is_active: boolean;
  activated_by: number | null;
  notes: string | null;
  created_at: string;
}

export interface SchoolUsageOverview {
  date: string;
  schools: {
    school_id: number | null;
    total_messages: number;
    total_tokens: number;
    active_users: number;
  }[];
}

export interface SubscriptionPlanCreate {
  name: string;
  display_name: string;
  daily_message_limit?: number | null;
  feature_limits?: Record<string, number>;
  description?: string | null;
  sort_order?: number;
  price_monthly_kzt?: number | null;
  price_yearly_kzt?: number | null;
}

export interface SubscriptionPlanUpdate {
  display_name?: string;
  daily_message_limit?: number | null;
  feature_limits?: Record<string, number>;
  description?: string;
  is_active?: boolean;
  sort_order?: number;
  price_monthly_kzt?: number | null;
  price_yearly_kzt?: number | null;
}

export interface SchoolSubscriptionCreate {
  school_id: number;
  plan_id: number;
  expires_at?: string | null;
  limit_overrides?: Record<string, number> | null;
  notes?: string | null;
}

export interface SchoolSubscriptionUpdate {
  plan_id?: number;
  expires_at?: string | null;
  limit_overrides?: Record<string, number> | null;
  is_active?: boolean;
  notes?: string | null;
}

const BASE = '/admin/global/subscriptions';

export const subscriptionsApi = {
  // Plans
  listPlans: async (activeOnly = true): Promise<SubscriptionPlan[]> => {
    const { data } = await apiClient.get<SubscriptionPlan[]>(`${BASE}/plans`, {
      params: { active_only: activeOnly },
    });
    return data;
  },

  createPlan: async (plan: SubscriptionPlanCreate): Promise<SubscriptionPlan> => {
    const { data } = await apiClient.post<SubscriptionPlan>(`${BASE}/plans`, plan);
    return data;
  },

  updatePlan: async (id: number, plan: SubscriptionPlanUpdate): Promise<SubscriptionPlan> => {
    const { data } = await apiClient.put<SubscriptionPlan>(`${BASE}/plans/${id}`, plan);
    return data;
  },

  // School Subscriptions
  listSchoolSubscriptions: async (): Promise<SchoolSubscription[]> => {
    const { data } = await apiClient.get<SchoolSubscription[]>(`${BASE}/schools`);
    return data;
  },

  assignPlan: async (sub: SchoolSubscriptionCreate): Promise<SchoolSubscription> => {
    const { data } = await apiClient.post<SchoolSubscription>(`${BASE}/schools`, sub);
    return data;
  },

  updateSubscription: async (id: number, sub: SchoolSubscriptionUpdate): Promise<SchoolSubscription> => {
    const { data } = await apiClient.put<SchoolSubscription>(`${BASE}/schools/${id}`, sub);
    return data;
  },

  // Usage
  getUsageOverview: async (usageDate?: string): Promise<SchoolUsageOverview> => {
    const { data } = await apiClient.get<SchoolUsageOverview>(`${BASE}/usage`, {
      params: usageDate ? { usage_date: usageDate } : undefined,
    });
    return data;
  },
};
