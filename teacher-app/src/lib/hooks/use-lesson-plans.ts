import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  generateLessonPlan,
  saveLessonPlan,
  listLessonPlans,
  getLessonPlan,
  updateLessonPlan,
  deleteLessonPlan,
} from '@/lib/api/lesson-plans';
import type {
  LessonPlanGenerateRequest,
  LessonPlanGenerateResponse,
  LessonPlanSaveRequest,
  LessonPlanFullResponse,
  LessonPlanListItem,
  LessonPlanUpdateRequest,
} from '@/types/lesson-plan';

export function useGenerateLessonPlan() {
  return useMutation<
    LessonPlanGenerateResponse,
    Error,
    LessonPlanGenerateRequest
  >({
    mutationFn: generateLessonPlan,
  });
}

export function useSaveLessonPlan() {
  const queryClient = useQueryClient();
  return useMutation<LessonPlanFullResponse, Error, LessonPlanSaveRequest>({
    mutationFn: saveLessonPlan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lesson-plans'] });
    },
  });
}

export function useLessonPlans(skip = 0, limit = 20) {
  return useQuery<LessonPlanListItem[]>({
    queryKey: ['lesson-plans', skip, limit],
    queryFn: () => listLessonPlans(skip, limit),
  });
}

export function useLessonPlan(id: number | null) {
  return useQuery<LessonPlanFullResponse>({
    queryKey: ['lesson-plans', id],
    queryFn: () => getLessonPlan(id!),
    enabled: !!id,
  });
}

export function useUpdateLessonPlan() {
  const queryClient = useQueryClient();
  return useMutation<
    LessonPlanFullResponse,
    Error,
    { id: number; data: LessonPlanUpdateRequest }
  >({
    mutationFn: ({ id, data }) => updateLessonPlan(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['lesson-plans', id] });
      queryClient.invalidateQueries({ queryKey: ['lesson-plans'] });
    },
  });
}

export function useDeleteLessonPlan() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, number>({
    mutationFn: deleteLessonPlan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lesson-plans'] });
    },
  });
}
