import { apiClient } from './client';
import type {
  LessonPlanGenerateRequest,
  LessonPlanGenerateResponse,
  LessonPlanSaveRequest,
  LessonPlanFullResponse,
  LessonPlanListItem,
  LessonPlanUpdateRequest,
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

export async function saveLessonPlan(
  data: LessonPlanSaveRequest
): Promise<LessonPlanFullResponse> {
  const response = await apiClient.post('/teachers/lesson-plans', data);
  return response.data;
}

export async function listLessonPlans(
  skip = 0,
  limit = 20
): Promise<LessonPlanListItem[]> {
  const response = await apiClient.get('/teachers/lesson-plans', {
    params: { skip, limit },
  });
  return response.data;
}

export async function getLessonPlan(
  id: number
): Promise<LessonPlanFullResponse> {
  const response = await apiClient.get(`/teachers/lesson-plans/${id}`);
  return response.data;
}

export async function updateLessonPlan(
  id: number,
  data: LessonPlanUpdateRequest
): Promise<LessonPlanFullResponse> {
  const response = await apiClient.put(`/teachers/lesson-plans/${id}`, data);
  return response.data;
}

export async function deleteLessonPlan(id: number): Promise<void> {
  await apiClient.delete(`/teachers/lesson-plans/${id}`);
}

export async function exportLessonPlanDocx(id: number): Promise<void> {
  const response = await apiClient.get(
    `/teachers/lesson-plans/${id}/export/docx`,
    { responseType: 'blob' }
  );
  const blob = new Blob([response.data], {
    type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `lesson_plan_${id}.docx`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}
