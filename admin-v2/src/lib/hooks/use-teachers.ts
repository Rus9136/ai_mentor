import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { teachersApi } from '@/lib/api/teachers';
import type { Teacher, TeacherCreate, TeacherUpdate } from '@/types';
import { toast } from 'sonner';

// Query keys factory
export const teacherKeys = {
  all: ['school-teachers'] as const,
  lists: () => [...teacherKeys.all, 'list'] as const,
  list: (filters?: Record<string, unknown>) => [...teacherKeys.lists(), filters] as const,
  details: () => [...teacherKeys.all, 'detail'] as const,
  detail: (id: number) => [...teacherKeys.details(), id] as const,
};

// Get all teachers
export function useTeachers() {
  return useQuery({
    queryKey: teacherKeys.lists(),
    queryFn: teachersApi.getList,
  });
}

// Get single teacher by ID
export function useTeacher(id: number, enabled = true) {
  return useQuery({
    queryKey: teacherKeys.detail(id),
    queryFn: () => teachersApi.getOne(id),
    enabled: enabled && id > 0,
  });
}

// Create teacher mutation
export function useCreateTeacher() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TeacherCreate) => teachersApi.create(data),
    onSuccess: (newTeacher) => {
      queryClient.invalidateQueries({ queryKey: teacherKeys.lists() });
      const name = newTeacher.user?.first_name || 'Учитель';
      toast.success(`${name} добавлен`);
    },
    onError: (error: Error) => {
      toast.error(`Ошибка создания: ${error.message}`);
    },
  });
}

// Update teacher mutation
export function useUpdateTeacher() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: TeacherUpdate }) =>
      teachersApi.update(id, data),
    onSuccess: (updatedTeacher) => {
      queryClient.invalidateQueries({ queryKey: teacherKeys.lists() });
      queryClient.invalidateQueries({
        queryKey: teacherKeys.detail(updatedTeacher.id),
      });
      toast.success('Данные учителя обновлены');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка обновления: ${error.message}`);
    },
  });
}

// Delete teacher mutation
export function useDeleteTeacher() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => teachersApi.delete(id),
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({ queryKey: teacherKeys.lists() });
      queryClient.removeQueries({ queryKey: teacherKeys.detail(deletedId) });
      toast.success('Учитель удален');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка удаления: ${error.message}`);
    },
  });
}
