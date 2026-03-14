import { apiClient } from './client';
import type { JoinQuizResponse } from '@/types/quiz';

export async function joinQuiz(join_code: string): Promise<JoinQuizResponse> {
  const response = await apiClient.post<JoinQuizResponse>('/students/quiz-sessions/join', { join_code });
  return response.data;
}

export async function getQuizResults(sessionId: number) {
  const response = await apiClient.get(`/students/quiz-sessions/${sessionId}/results`);
  return response.data;
}
