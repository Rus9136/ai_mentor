import { apiClient } from './client';

export interface CustomQuestion {
  question_text: string;
  options: string[];
  correct_option: number;
}

export interface QuizSessionCreate {
  test_id?: number;
  question_ids?: number[];
  custom_questions?: CustomQuestion[];
  class_id?: number;
  settings?: {
    time_per_question_ms?: number;
    shuffle_questions?: boolean;
    shuffle_answers?: boolean;
    scoring_mode?: 'speed' | 'accuracy';
    mode?: 'classic' | 'team' | 'self_paced' | 'quick_question';
    pacing?: 'timed' | 'teacher_paced';
    team_count?: number;
    show_space_race?: boolean;
    deadline?: string;
  };
}

export interface QuestionOptionPreview {
  text: string;
  is_correct: boolean;
}

export interface QuestionPreview {
  id: number;
  question_text: string;
  question_type: string;
  options: QuestionOptionPreview[];
}

export interface ParagraphQuestions {
  paragraph_id: number;
  paragraph_number: number;
  paragraph_title: string;
  questions: QuestionPreview[];
}

export interface QuickQuestionCreate {
  class_id?: number;
  question_text: string;
  options: string[];
  time_per_question_ms?: number;
}

export async function createQuizSession(data: QuizSessionCreate) {
  const response = await apiClient.post('/teachers/quiz-sessions/', data);
  return response.data;
}

export async function getQuizSessions(params?: { status?: string }) {
  const response = await apiClient.get('/teachers/quiz-sessions/', { params });
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

export async function getChapterQuestions(chapterId: number): Promise<ParagraphQuestions[]> {
  const response = await apiClient.get('/teachers/quiz-sessions/chapter-questions', {
    params: { chapter_id: chapterId },
  });
  return response.data;
}

export async function createQuickQuestion(data: QuickQuestionCreate) {
  const response = await apiClient.post('/teachers/quiz-sessions/quick-question', data);
  return response.data;
}

export async function getStudentProgress(sessionId: number) {
  const response = await apiClient.get(`/teachers/quiz-sessions/${sessionId}/student-progress`);
  return response.data;
}

export async function getTeamLeaderboard(sessionId: number) {
  const response = await apiClient.get(`/teachers/quiz-sessions/${sessionId}/team-leaderboard`);
  return response.data;
}

export async function getQuizMatrix(sessionId: number) {
  const response = await apiClient.get(`/teachers/quiz-sessions/${sessionId}/matrix`);
  return response.data;
}

export async function downloadReport(sessionId: number, type: 'class' | 'questions') {
  const response = await apiClient.get(`/teachers/quiz-sessions/${sessionId}/reports/${type}`, {
    responseType: 'blob',
  });
  return response.data;
}

export async function downloadTrendReport(classId: number) {
  const response = await apiClient.get('/teachers/quiz-sessions/reports/trend', {
    params: { class_id: classId },
    responseType: 'blob',
  });
  return response.data;
}
