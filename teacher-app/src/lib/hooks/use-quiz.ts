import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  createQuizSession,
  getQuizSessions,
  getQuizSession,
  startQuiz,
  cancelQuiz,
  getQuizResults,
  getTestsForQuiz,
  type QuizSessionCreate,
} from '@/lib/api/quiz';

export const quizKeys = {
  all: ['quiz'] as const,
  lists: () => [...quizKeys.all, 'list'] as const,
  list: (params?: { status?: string }) => [...quizKeys.lists(), params] as const,
  details: () => [...quizKeys.all, 'detail'] as const,
  detail: (id: number) => [...quizKeys.details(), id] as const,
  results: (id: number) => [...quizKeys.all, 'results', id] as const,
  tests: (params?: Record<string, unknown>) => [...quizKeys.all, 'tests', params] as const,
};

export function useQuizSessions(params?: { status?: string }) {
  return useQuery({
    queryKey: quizKeys.list(params),
    queryFn: () => getQuizSessions(params),
  });
}

export function useQuizSession(sessionId: number) {
  return useQuery({
    queryKey: quizKeys.detail(sessionId),
    queryFn: () => getQuizSession(sessionId),
    enabled: sessionId > 0,
    refetchInterval: 5000,
  });
}

export function useQuizResults(sessionId: number) {
  return useQuery({
    queryKey: quizKeys.results(sessionId),
    queryFn: () => getQuizResults(sessionId),
    enabled: sessionId > 0,
  });
}

export function useTestsForQuiz(params: { paragraph_id?: number; chapter_id?: number }) {
  return useQuery({
    queryKey: quizKeys.tests(params),
    queryFn: () => getTestsForQuiz(params),
    enabled: !!(params.paragraph_id || params.chapter_id),
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
