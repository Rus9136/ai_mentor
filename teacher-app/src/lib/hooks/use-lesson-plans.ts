import { useMutation } from '@tanstack/react-query';
import { generateLessonPlan } from '@/lib/api/lesson-plans';
import type {
  LessonPlanGenerateRequest,
  LessonPlanGenerateResponse,
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
