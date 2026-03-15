import { apiClient } from './client';
import type { JoinQuizResponse, SelfPacedNextQuestion, SelfPacedAnswerResult, StudentQuizListItem } from '@/types/quiz';

export async function getMyQuizzes(): Promise<StudentQuizListItem[]> {
  const response = await apiClient.get<StudentQuizListItem[]>('/students/quiz-sessions/my-quizzes');
  return response.data;
}

export async function joinQuiz(join_code: string): Promise<JoinQuizResponse> {
  const response = await apiClient.post<JoinQuizResponse>('/students/quiz-sessions/join', { join_code });
  return response.data;
}

export async function getQuizResults(sessionId: number) {
  const response = await apiClient.get(`/students/quiz-sessions/${sessionId}/results`);
  return response.data;
}

// Self-paced mode endpoints

export async function getNextQuestion(sessionId: number): Promise<SelfPacedNextQuestion> {
  const response = await apiClient.get<SelfPacedNextQuestion>(
    `/students/quiz-sessions/${sessionId}/next-question`,
  );
  return response.data;
}

export async function submitSelfPacedAnswer(
  sessionId: number,
  questionIndex: number,
  selectedOption: number,
): Promise<SelfPacedAnswerResult> {
  const response = await apiClient.post<SelfPacedAnswerResult>(
    `/students/quiz-sessions/${sessionId}/submit-answer`,
    { question_index: questionIndex, selected_option: selectedOption },
  );
  return response.data;
}
