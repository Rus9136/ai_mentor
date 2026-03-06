import { apiClient } from './client';
import type {
  LessonPlanGenerateRequest,
  LessonPlanGenerateResponse,
} from '@/types/lesson-plan';

export async function generateLessonPlan(
  data: LessonPlanGenerateRequest
): Promise<LessonPlanGenerateResponse> {
  const response = await apiClient.post(
    '/teachers/lesson-plans/generate',
    data
  );
  return response.data;
}
