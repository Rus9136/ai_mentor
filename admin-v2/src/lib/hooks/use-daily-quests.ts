import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { dailyQuestsApi, DailyQuestCreate, DailyQuestUpdate } from '@/lib/api/daily-quests';
import { toast } from 'sonner';

export const dailyQuestKeys = {
  all: ['daily-quests'] as const,
  lists: () => [...dailyQuestKeys.all, 'list'] as const,
  list: (role: string) => [...dailyQuestKeys.lists(), role] as const,
  details: () => [...dailyQuestKeys.all, 'detail'] as const,
  detail: (id: number, role: string) => [...dailyQuestKeys.details(), id, role] as const,
};

export function useDailyQuests(role: string) {
  return useQuery({
    queryKey: dailyQuestKeys.list(role),
    queryFn: () => dailyQuestsApi.getList(role),
  });
}

export function useDailyQuest(id: number, role: string, enabled = true) {
  return useQuery({
    queryKey: dailyQuestKeys.detail(id, role),
    queryFn: () => dailyQuestsApi.getOne(id, role),
    enabled: enabled && id > 0,
  });
}

export function useCreateDailyQuest(role: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: DailyQuestCreate) => dailyQuestsApi.create(data, role),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: dailyQuestKeys.lists() });
      toast.success('Квест создан');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка создания: ${error.message}`);
    },
  });
}

export function useUpdateDailyQuest(role: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: DailyQuestUpdate }) =>
      dailyQuestsApi.update(id, data, role),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: dailyQuestKeys.lists() });
      toast.success('Квест обновлен');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка обновления: ${error.message}`);
    },
  });
}

export function useDeleteDailyQuest(role: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => dailyQuestsApi.delete(id, role),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: dailyQuestKeys.lists() });
      toast.success('Квест деактивирован');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка удаления: ${error.message}`);
    },
  });
}
