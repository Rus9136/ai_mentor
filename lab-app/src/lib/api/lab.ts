import { apiClient } from './client';
import type { Lab, LabProgress, LabTask, LabTaskAnswerResponse } from '@/types/lab';

export async function getAvailableLabs(): Promise<Lab[]> {
  const response = await apiClient.get<Lab[]>('/students/lab/available');
  return response.data;
}

export async function getLab(labId: number): Promise<Lab> {
  const response = await apiClient.get<Lab>(`/students/lab/${labId}`);
  return response.data;
}

export async function getLabProgress(labId: number): Promise<LabProgress | null> {
  try {
    const response = await apiClient.get<LabProgress>(`/students/lab/${labId}/progress`);
    return response.data;
  } catch {
    return null;
  }
}

export async function updateLabProgress(
  labId: number,
  progressData: Record<string, unknown>
): Promise<LabProgress> {
  const response = await apiClient.post<LabProgress>(`/students/lab/${labId}/progress`, progressData);
  return response.data;
}

export async function getLabTasks(labId: number): Promise<LabTask[]> {
  const response = await apiClient.get<LabTask[]>(`/students/lab/${labId}/tasks`);
  return response.data;
}

export async function submitTaskAnswer(
  labId: number,
  taskId: number,
  answerData: Record<string, unknown>
): Promise<LabTaskAnswerResponse> {
  const response = await apiClient.post<LabTaskAnswerResponse>(
    `/students/lab/${labId}/tasks/${taskId}/answer`,
    answerData
  );
  return response.data;
}
