import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { studentsApi } from '@/lib/api/students';
import type { Student, StudentCreate, StudentUpdate } from '@/types';
import { toast } from 'sonner';

// Query keys factory
export const studentKeys = {
  all: ['school-students'] as const,
  lists: () => [...studentKeys.all, 'list'] as const,
  list: (filters?: Record<string, unknown>) => [...studentKeys.lists(), filters] as const,
  details: () => [...studentKeys.all, 'detail'] as const,
  detail: (id: number) => [...studentKeys.details(), id] as const,
};

// Get all students
export function useStudents() {
  return useQuery({
    queryKey: studentKeys.lists(),
    queryFn: studentsApi.getList,
  });
}

// Get single student by ID
export function useStudent(id: number, enabled = true) {
  return useQuery({
    queryKey: studentKeys.detail(id),
    queryFn: () => studentsApi.getOne(id),
    enabled: enabled && id > 0,
  });
}

// Create student mutation
export function useCreateStudent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: StudentCreate) => studentsApi.create(data),
    onSuccess: (newStudent) => {
      queryClient.invalidateQueries({ queryKey: studentKeys.lists() });
      const name = newStudent.user?.first_name || 'Ученик';
      toast.success(`${name} добавлен`);
    },
    onError: (error: Error) => {
      toast.error(`Ошибка создания: ${error.message}`);
    },
  });
}

// Update student mutation
export function useUpdateStudent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: StudentUpdate }) =>
      studentsApi.update(id, data),
    onSuccess: (updatedStudent) => {
      queryClient.invalidateQueries({ queryKey: studentKeys.lists() });
      queryClient.invalidateQueries({
        queryKey: studentKeys.detail(updatedStudent.id),
      });
      toast.success('Данные ученика обновлены');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка обновления: ${error.message}`);
    },
  });
}

// Delete student mutation
export function useDeleteStudent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => studentsApi.delete(id),
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({ queryKey: studentKeys.lists() });
      queryClient.removeQueries({ queryKey: studentKeys.detail(deletedId) });
      toast.success('Ученик удален');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка удаления: ${error.message}`);
    },
  });
}
