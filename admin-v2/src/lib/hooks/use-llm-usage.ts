import { useQuery } from '@tanstack/react-query';
import { llmUsageApi } from '@/lib/api/llm-usage';

interface DateRange {
  date_from?: string;
  date_to?: string;
}

export const llmUsageKeys = {
  all: ['llm-usage'] as const,
  stats: (params?: DateRange) => [...llmUsageKeys.all, 'stats', params] as const,
  daily: (params?: DateRange) => [...llmUsageKeys.all, 'daily', params] as const,
  bySchool: (params?: DateRange) => [...llmUsageKeys.all, 'by-school', params] as const,
};

export function useLLMUsageStats(params?: DateRange) {
  return useQuery({
    queryKey: llmUsageKeys.stats(params),
    queryFn: () => llmUsageApi.getStats(params),
  });
}

export function useLLMUsageDaily(params?: DateRange) {
  return useQuery({
    queryKey: llmUsageKeys.daily(params),
    queryFn: () => llmUsageApi.getDaily(params),
  });
}

export function useLLMUsageBySchool(params?: DateRange) {
  return useQuery({
    queryKey: llmUsageKeys.bySchool(params),
    queryFn: () => llmUsageApi.getBySchool(params),
  });
}
