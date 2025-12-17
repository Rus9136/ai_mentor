import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { schoolsApi } from '@/lib/api/schools';
import type { School, SchoolCreate, SchoolUpdate } from '@/types';
import { toast } from 'sonner';

// Query keys factory for proper cache invalidation
export const schoolKeys = {
  all: ['schools'] as const,
  lists: () => [...schoolKeys.all, 'list'] as const,
  list: (filters?: Record<string, unknown>) =>
    [...schoolKeys.lists(), filters] as const,
  details: () => [...schoolKeys.all, 'detail'] as const,
  detail: (id: number) => [...schoolKeys.details(), id] as const,
};

// Get all schools
export function useSchools() {
  return useQuery({
    queryKey: schoolKeys.lists(),
    queryFn: schoolsApi.getList,
  });
}

// Get single school by ID
export function useSchool(id: number, enabled = true) {
  return useQuery({
    queryKey: schoolKeys.detail(id),
    queryFn: () => schoolsApi.getOne(id),
    enabled: enabled && id > 0,
  });
}

// Create school mutation
export function useCreateSchool() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SchoolCreate) => schoolsApi.create(data),
    onSuccess: (newSchool) => {
      queryClient.invalidateQueries({ queryKey: schoolKeys.lists() });
      toast.success(`Школа "${newSchool.name}" создана`);
    },
    onError: (error: Error) => {
      toast.error(`Ошибка создания: ${error.message}`);
    },
  });
}

// Update school mutation
export function useUpdateSchool() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: SchoolUpdate }) =>
      schoolsApi.update(id, data),
    onSuccess: (updatedSchool) => {
      queryClient.invalidateQueries({ queryKey: schoolKeys.lists() });
      queryClient.invalidateQueries({
        queryKey: schoolKeys.detail(updatedSchool.id),
      });
      toast.success(`Школа "${updatedSchool.name}" обновлена`);
    },
    onError: (error: Error) => {
      toast.error(`Ошибка обновления: ${error.message}`);
    },
  });
}

// Delete school mutation
export function useDeleteSchool() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => schoolsApi.delete(id),
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({ queryKey: schoolKeys.lists() });
      queryClient.removeQueries({ queryKey: schoolKeys.detail(deletedId) });
      toast.success('Школа удалена');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка удаления: ${error.message}`);
    },
  });
}

// Block school mutation
export function useBlockSchool() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => schoolsApi.block(id),
    onSuccess: (updatedSchool) => {
      queryClient.invalidateQueries({ queryKey: schoolKeys.lists() });
      queryClient.invalidateQueries({
        queryKey: schoolKeys.detail(updatedSchool.id),
      });
      toast.success(`Школа "${updatedSchool.name}" заблокирована`);
    },
    onError: (error: Error) => {
      toast.error(`Ошибка блокировки: ${error.message}`);
    },
  });
}

// Unblock school mutation
export function useUnblockSchool() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => schoolsApi.unblock(id),
    onSuccess: (updatedSchool) => {
      queryClient.invalidateQueries({ queryKey: schoolKeys.lists() });
      queryClient.invalidateQueries({
        queryKey: schoolKeys.detail(updatedSchool.id),
      });
      toast.success(`Школа "${updatedSchool.name}" разблокирована`);
    },
    onError: (error: Error) => {
      toast.error(`Ошибка разблокировки: ${error.message}`);
    },
  });
}

// Bulk block schools mutation
export function useBulkBlockSchools() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (ids: number[]) => {
      const results = await Promise.all(ids.map((id) => schoolsApi.block(id)));
      return results;
    },
    onSuccess: (_, ids) => {
      queryClient.invalidateQueries({ queryKey: schoolKeys.lists() });
      toast.success(`${ids.length} школ(ы) заблокированы`);
    },
    onError: (error: Error) => {
      toast.error(`Ошибка блокировки: ${error.message}`);
    },
  });
}

// Bulk unblock schools mutation
export function useBulkUnblockSchools() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (ids: number[]) => {
      const results = await Promise.all(
        ids.map((id) => schoolsApi.unblock(id))
      );
      return results;
    },
    onSuccess: (_, ids) => {
      queryClient.invalidateQueries({ queryKey: schoolKeys.lists() });
      toast.success(`${ids.length} школ(ы) разблокированы`);
    },
    onError: (error: Error) => {
      toast.error(`Ошибка разблокировки: ${error.message}`);
    },
  });
}
