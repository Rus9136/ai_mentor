import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { parentsApi } from '@/lib/api/parents';
import type { Parent, ParentCreate } from '@/types';
import { toast } from 'sonner';
import { studentKeys } from './use-students';

// Query keys factory
export const parentKeys = {
  all: ['school-parents'] as const,
  lists: () => [...parentKeys.all, 'list'] as const,
  list: (filters?: Record<string, unknown>) => [...parentKeys.lists(), filters] as const,
  details: () => [...parentKeys.all, 'detail'] as const,
  detail: (id: number) => [...parentKeys.details(), id] as const,
  children: (id: number) => [...parentKeys.detail(id), 'children'] as const,
};

// Get all parents
export function useParents() {
  return useQuery({
    queryKey: parentKeys.lists(),
    queryFn: parentsApi.getList,
  });
}

// Get single parent by ID
export function useParent(id: number, enabled = true) {
  return useQuery({
    queryKey: parentKeys.detail(id),
    queryFn: () => parentsApi.getOne(id),
    enabled: enabled && id > 0,
  });
}

// Get parent's children
export function useParentChildren(parentId: number, enabled = true) {
  return useQuery({
    queryKey: parentKeys.children(parentId),
    queryFn: () => parentsApi.getChildren(parentId),
    enabled: enabled && parentId > 0,
  });
}

// Create parent mutation
export function useCreateParent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ParentCreate) => parentsApi.create(data),
    onSuccess: (newParent) => {
      queryClient.invalidateQueries({ queryKey: parentKeys.lists() });
      const name = newParent.user?.first_name || 'Родитель';
      toast.success(`${name} добавлен`);
    },
    onError: (error: Error) => {
      toast.error(`Ошибка создания: ${error.message}`);
    },
  });
}

// Delete parent mutation
export function useDeleteParent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => parentsApi.delete(id),
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({ queryKey: parentKeys.lists() });
      queryClient.removeQueries({ queryKey: parentKeys.detail(deletedId) });
      toast.success('Родитель удален');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка удаления: ${error.message}`);
    },
  });
}

// Add children to parent
export function useAddChildren() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ parentId, studentIds }: { parentId: number; studentIds: number[] }) =>
      parentsApi.addChildren(parentId, studentIds),
    onSuccess: (_, { parentId }) => {
      queryClient.invalidateQueries({ queryKey: parentKeys.detail(parentId) });
      queryClient.invalidateQueries({ queryKey: parentKeys.children(parentId) });
      queryClient.invalidateQueries({ queryKey: studentKeys.lists() });
      toast.success('Дети добавлены');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка добавления: ${error.message}`);
    },
  });
}

// Remove child from parent
export function useRemoveChild() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ parentId, studentId }: { parentId: number; studentId: number }) =>
      parentsApi.removeChild(parentId, studentId),
    onSuccess: (_, { parentId }) => {
      queryClient.invalidateQueries({ queryKey: parentKeys.detail(parentId) });
      queryClient.invalidateQueries({ queryKey: parentKeys.children(parentId) });
      queryClient.invalidateQueries({ queryKey: studentKeys.lists() });
      toast.success('Ребенок удален из списка');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка удаления: ${error.message}`);
    },
  });
}
