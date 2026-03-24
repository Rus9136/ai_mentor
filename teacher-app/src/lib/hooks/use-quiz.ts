import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  createQuizSession,
  getQuizSessions,
  getQuizSession,
  startQuiz,
  cancelQuiz,
  getQuizResults,
  getTestsForQuiz,
  getChapterQuestions,
  getStudentProgress,
  getTeamLeaderboard,
  getQuizMatrix,
  createQuickQuestion,
  createFactileSession,
  type QuizSessionCreate,
  type QuickQuestionCreate,
  type FactileCreateData,
} from '@/lib/api/quiz';

export const quizKeys = {
  all: ['quiz'] as const,
  lists: () => [...quizKeys.all, 'list'] as const,
  list: (params?: { status?: string }) => [...quizKeys.lists(), params] as const,
  details: () => [...quizKeys.all, 'detail'] as const,
  detail: (id: number) => [...quizKeys.details(), id] as const,
  results: (id: number) => [...quizKeys.all, 'results', id] as const,
  tests: (params?: Record<string, unknown>) => [...quizKeys.all, 'tests', params] as const,
  studentProgress: (id: number) => [...quizKeys.all, 'student-progress', id] as const,
  teamLeaderboard: (id: number) => [...quizKeys.all, 'team-leaderboard', id] as const,
  matrix: (id: number) => [...quizKeys.all, 'matrix', id] as const,
};

export function useQuizSessions(params?: { status?: string }) {
  return useQuery({
    queryKey: quizKeys.list(params),
    queryFn: () => getQuizSessions(params),
  });
}

const ACTIVE_STATUSES = ['lobby', 'in_progress'];

export function useQuizSession(sessionId: number) {
  return useQuery({
    queryKey: quizKeys.detail(sessionId),
    queryFn: () => getQuizSession(sessionId),
    enabled: sessionId > 0,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && ACTIVE_STATUSES.includes(status) ? 5000 : false;
    },
  });
}

export function useQuizResults(sessionId: number, status?: string) {
  return useQuery({
    queryKey: quizKeys.results(sessionId),
    queryFn: () => getQuizResults(sessionId),
    enabled: sessionId > 0 && status === 'finished',
  });
}

export function useTestsForQuiz(params: { paragraph_id?: number; chapter_id?: number }) {
  return useQuery({
    queryKey: quizKeys.tests(params),
    queryFn: () => getTestsForQuiz(params),
    enabled: !!(params.paragraph_id || params.chapter_id),
  });
}

export function useChapterQuestions(chapterId?: number) {
  return useQuery({
    queryKey: [...quizKeys.all, 'chapter-questions', chapterId] as const,
    queryFn: () => getChapterQuestions(chapterId!),
    enabled: !!chapterId,
  });
}

export function useCreateQuiz() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: QuizSessionCreate) => createQuizSession(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: quizKeys.lists() });
    },
  });
}

export function useStartQuiz() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: number) => startQuiz(sessionId),
    onSuccess: (_, sessionId) => {
      queryClient.invalidateQueries({ queryKey: quizKeys.detail(sessionId) });
    },
  });
}

export function useCancelQuiz() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: number) => cancelQuiz(sessionId),
    onSuccess: (_, sessionId) => {
      queryClient.invalidateQueries({ queryKey: quizKeys.detail(sessionId) });
      queryClient.invalidateQueries({ queryKey: quizKeys.lists() });
    },
  });
}

export function useStudentProgress(sessionId: number, status?: string) {
  return useQuery({
    queryKey: quizKeys.studentProgress(sessionId),
    queryFn: () => getStudentProgress(sessionId),
    enabled: sessionId > 0,
    refetchInterval: status && ACTIVE_STATUSES.includes(status) ? 5000 : false,
  });
}

export function useTeamLeaderboard(sessionId: number, status?: string) {
  return useQuery({
    queryKey: quizKeys.teamLeaderboard(sessionId),
    queryFn: () => getTeamLeaderboard(sessionId),
    enabled: sessionId > 0,
    refetchInterval: status && ACTIVE_STATUSES.includes(status) ? 5000 : false,
  });
}

export function useQuizMatrix(sessionId: number, status?: string) {
  return useQuery({
    queryKey: quizKeys.matrix(sessionId),
    queryFn: () => getQuizMatrix(sessionId),
    enabled: sessionId > 0,
    refetchInterval: status && ACTIVE_STATUSES.includes(status) ? 5000 : false,
  });
}

export function useCreateFactile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: FactileCreateData) => createFactileSession(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: quizKeys.lists() });
    },
  });
}

export function useCreateQuickQuestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: QuickQuestionCreate) => createQuickQuestion(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: quizKeys.lists() });
    },
  });
}
