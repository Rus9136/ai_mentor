import { apiClient } from './client';

export interface QuizSessionCreate {
  test_id: number;
  class_id?: number;
  settings?: { time_per_question_ms?: number };
}

export async function createQuizSession(data: QuizSessionCreate) {
  const response = await apiClient.post('/teachers/quiz-sessions', data);
  return response.data;
}

export async function getQuizSessions(params?: { status?: string }) {
  const response = await apiClient.get('/teachers/quiz-sessions', { params });
  return response.data;
}

export async function getQuizSession(sessionId: number) {
  const response = await apiClient.get(`/teachers/quiz-sessions/${sessionId}`);
  return response.data;
}

export async function startQuiz(sessionId: number) {
  const response = await apiClient.patch(`/teachers/quiz-sessions/${sessionId}/start`);
  return response.data;
}

export async function cancelQuiz(sessionId: number) {
  const response = await apiClient.patch(`/teachers/quiz-sessions/${sessionId}/cancel`);
  return response.data;
}

export async function getQuizResults(sessionId: number) {
  const response = await apiClient.get(`/teachers/quiz-sessions/${sessionId}/results`);
  return response.data;
}

export async function getTestsForQuiz(params: { paragraph_id?: number; chapter_id?: number }) {
  const response = await apiClient.get('/teachers/quiz-sessions/tests', { params });
  return response.data;
}
