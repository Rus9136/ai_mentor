import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { classesApi } from '@/lib/api/classes';
import type { SchoolClass, SchoolClassCreate, SchoolClassUpdate } from '@/types';
import { toast } from 'sonner';
import { studentKeys } from './use-students';
import { teacherKeys } from './use-teachers';

// Query keys factory
export const classKeys = {
  all: ['school-classes'] as const,
  lists: () => [...classKeys.all, 'list'] as const,
  list: (filters?: Record<string, unknown>) => [...classKeys.lists(), filters] as const,
  details: () => [...classKeys.all, 'detail'] as const,
  detail: (id: number) => [...classKeys.details(), id] as const,
};

// Get all classes
export function useClasses() {
  return useQuery({
    queryKey: classKeys.lists(),
    queryFn: classesApi.getList,
  });
}

// Get single class by ID
export function useClass(id: number, enabled = true) {
  return useQuery({
    queryKey: classKeys.detail(id),
    queryFn: () => classesApi.getOne(id),
    enabled: enabled && id > 0,
  });
}

// Create class mutation
export function useCreateClass() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SchoolClassCreate) => classesApi.create(data),
    onSuccess: (newClass) => {
      queryClient.invalidateQueries({ queryKey: classKeys.lists() });
      toast.success(`Класс "${newClass.name}" создан`);
    },
    onError: (error: Error) => {
      toast.error(`Ошибка создания: ${error.message}`);
    },
  });
}

// Update class mutation
export function useUpdateClass() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: SchoolClassUpdate }) =>
      classesApi.update(id, data),
    onSuccess: (updatedClass) => {
      queryClient.invalidateQueries({ queryKey: classKeys.lists() });
      queryClient.invalidateQueries({
        queryKey: classKeys.detail(updatedClass.id),
      });
      toast.success(`Класс "${updatedClass.name}" обновлен`);
    },
    onError: (error: Error) => {
      toast.error(`Ошибка обновления: ${error.message}`);
    },
  });
}

// Delete class mutation
export function useDeleteClass() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => classesApi.delete(id),
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({ queryKey: classKeys.lists() });
      queryClient.removeQueries({ queryKey: classKeys.detail(deletedId) });
      toast.success('Класс удален');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка удаления: ${error.message}`);
    },
  });
}

// Add students to class
export function useAddStudentsToClass() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ classId, studentIds }: { classId: number; studentIds: number[] }) =>
      classesApi.addStudents(classId, studentIds),
    onSuccess: (_, { classId }) => {
      queryClient.invalidateQueries({ queryKey: classKeys.detail(classId) });
      queryClient.invalidateQueries({ queryKey: classKeys.lists() });
      queryClient.invalidateQueries({ queryKey: studentKeys.lists() });
      toast.success('Ученики добавлены в класс');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка добавления: ${error.message}`);
    },
  });
}

// Remove student from class
export function useRemoveStudentFromClass() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ classId, studentId }: { classId: number; studentId: number }) =>
      classesApi.removeStudent(classId, studentId),
    onSuccess: (_, { classId }) => {
      queryClient.invalidateQueries({ queryKey: classKeys.detail(classId) });
      queryClient.invalidateQueries({ queryKey: classKeys.lists() });
      queryClient.invalidateQueries({ queryKey: studentKeys.lists() });
      toast.success('Ученик удален из класса');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка удаления: ${error.message}`);
    },
  });
}

// Add teachers to class
export function useAddTeachersToClass() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ classId, teacherIds }: { classId: number; teacherIds: number[] }) =>
      classesApi.addTeachers(classId, teacherIds),
    onSuccess: (_, { classId }) => {
      queryClient.invalidateQueries({ queryKey: classKeys.detail(classId) });
      queryClient.invalidateQueries({ queryKey: classKeys.lists() });
      queryClient.invalidateQueries({ queryKey: teacherKeys.lists() });
      toast.success('Учителя добавлены в класс');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка добавления: ${error.message}`);
    },
  });
}

// Remove teacher from class
export function useRemoveTeacherFromClass() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ classId, teacherId }: { classId: number; teacherId: number }) =>
      classesApi.removeTeacher(classId, teacherId),
    onSuccess: (_, { classId }) => {
      queryClient.invalidateQueries({ queryKey: classKeys.detail(classId) });
      queryClient.invalidateQueries({ queryKey: classKeys.lists() });
      queryClient.invalidateQueries({ queryKey: teacherKeys.lists() });
      toast.success('Учитель удален из класса');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка удаления: ${error.message}`);
    },
  });
}
