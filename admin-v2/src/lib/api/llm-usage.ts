import { apiClient } from './client';

export interface FeatureBreakdown {
  feature: string;
  total_calls: number;
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  avg_latency_ms: number | null;
  error_count: number;
}

export interface ModelBreakdown {
  model: string;
  provider: string;
  total_calls: number;
  total_tokens: number;
}

export interface LLMUsageSummary {
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  total_tokens: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  avg_latency_ms: number | null;
  by_feature: FeatureBreakdown[];
  by_model: ModelBreakdown[];
}

export interface LLMUsageDailyStats {
  date: string;
  total_calls: number;
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  error_count: number;
}

export interface LLMUsageSchoolBreakdown {
  school_id: number | null;
  total_calls: number;
  total_tokens: number;
}

interface DateRange {
  date_from?: string;
  date_to?: string;
}

export const llmUsageApi = {
  getStats: async (params?: DateRange): Promise<LLMUsageSummary> => {
    const { data } = await apiClient.get<LLMUsageSummary>(
      '/admin/global/llm-usage/stats',
      { params }
    );
    return data;
  },

  getDaily: async (params?: DateRange): Promise<LLMUsageDailyStats[]> => {
    const { data } = await apiClient.get<LLMUsageDailyStats[]>(
      '/admin/global/llm-usage/daily',
      { params }
    );
    return data;
  },

  getBySchool: async (params?: DateRange): Promise<LLMUsageSchoolBreakdown[]> => {
    const { data } = await apiClient.get<LLMUsageSchoolBreakdown[]>(
      '/admin/global/llm-usage/by-school',
      { params }
    );
    return data;
  },
};
