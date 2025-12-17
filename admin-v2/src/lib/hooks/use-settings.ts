import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { settingsApi } from '@/lib/api/settings';
import type { SchoolUpdate } from '@/types';
import { toast } from 'sonner';

// Query keys factory
export const settingsKeys = {
  all: ['school-settings'] as const,
  school: () => [...settingsKeys.all, 'school'] as const,
};

// Get current school settings
export function useSchoolSettings() {
  return useQuery({
    queryKey: settingsKeys.school(),
    queryFn: settingsApi.getSchool,
  });
}

// Update school settings mutation
export function useUpdateSchoolSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SchoolUpdate) => settingsApi.updateSchool(data),
    onSuccess: (updatedSchool) => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.school() });
      toast.success(`Настройки "${updatedSchool.name}" сохранены`);
    },
    onError: (error: Error) => {
      toast.error(`Ошибка сохранения: ${error.message}`);
    },
  });
}
