/**
 * React Query hooks for school gradebook (journal).
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getClassGrades,
  createGrade,
  updateGrade,
  deleteGrade,
  getSubjects,
} from '@/lib/api/grades';
import type { GradeCreate, GradeUpdate, GradeFilterParams } from '@/types/grade';

// =============================================================================
// Query Keys
// =============================================================================

export const gradeKeys = {
  all: ['grades'] as const,
  classGrades: (classId: number, subjectId: number, params?: GradeFilterParams) =>
    [...gradeKeys.all, 'class', classId, subjectId, params] as const,
  subjects: () => ['subjects'] as const,
};

// =============================================================================
// Queries
// =============================================================================

export function useClassGrades(
  classId: number,
  subjectId: number,
  params?: GradeFilterParams
) {
  return useQuery({
    queryKey: gradeKeys.classGrades(classId, subjectId, params),
    queryFn: () => getClassGrades(classId, subjectId, params),
    enabled: !!classId && !!subjectId,
  });
}

export function useSubjects() {
  return useQuery({
    queryKey: gradeKeys.subjects(),
    queryFn: getSubjects,
  });
}

// =============================================================================
// Mutations
// =============================================================================

export function useCreateGrade() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: GradeCreate) => createGrade(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: gradeKeys.all });
    },
  });
}

export function useUpdateGrade() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ gradeId, data }: { gradeId: number; data: GradeUpdate }) =>
      updateGrade(gradeId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: gradeKeys.all });
    },
  });
}

export function useDeleteGrade() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (gradeId: number) => deleteGrade(gradeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: gradeKeys.all });
    },
  });
}
