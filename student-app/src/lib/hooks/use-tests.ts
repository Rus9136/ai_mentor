import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getTestsForParagraph,
  getTestsForChapter,
  startTest,
  submitTest,
  completeTest,
  getAttempt,
  answerTestQuestion,
  AvailableTest,
  TestAttemptDetail,
  TestAnswerResponse,
  AnswerSubmit,
  TestPurpose,
} from '@/lib/api/tests';
import { textbookKeys } from './use-textbooks';

// =============================================================================
// Query Keys Factory
// =============================================================================

export const testKeys = {
  all: ['tests'] as const,
  forParagraph: (paragraphId: number) => [...testKeys.all, 'paragraph', paragraphId] as const,
  forChapter: (chapterId: number, purpose?: TestPurpose) =>
    [...testKeys.all, 'chapter', chapterId, purpose] as const,
  attempt: (attemptId: number) => ['test-attempts', attemptId] as const,
  attempts: () => ['test-attempts'] as const,
};

// =============================================================================
// Hooks
// =============================================================================

/**
 * Hook to get the first available FORMATIVE test for a paragraph.
 * Returns the test if available, or null if no test exists.
 */
export function useParagraphTest(paragraphId: number | undefined) {
  return useQuery<AvailableTest | null, Error>({
    queryKey: testKeys.forParagraph(paragraphId!),
    queryFn: async () => {
      const tests = await getTestsForParagraph(paragraphId!);
      // Return the first active test, or null if none
      return tests.length > 0 ? tests[0] : null;
    },
    enabled: !!paragraphId,
  });
}

/**
 * Hook to get all available tests for a paragraph.
 */
export function useParagraphTests(paragraphId: number | undefined) {
  return useQuery<AvailableTest[], Error>({
    queryKey: testKeys.forParagraph(paragraphId!),
    queryFn: () => getTestsForParagraph(paragraphId!),
    enabled: !!paragraphId,
  });
}

/**
 * Hook to get tests for a chapter.
 */
export function useChapterTests(chapterId: number | undefined, testPurpose?: TestPurpose) {
  return useQuery<AvailableTest[], Error>({
    queryKey: testKeys.forChapter(chapterId!, testPurpose),
    queryFn: () => getTestsForChapter(chapterId!, testPurpose),
    enabled: !!chapterId,
  });
}

/**
 * Hook to get a specific test attempt.
 */
export function useTestAttempt(attemptId: number | undefined) {
  return useQuery<TestAttemptDetail, Error>({
    queryKey: testKeys.attempt(attemptId!),
    queryFn: () => getAttempt(attemptId!),
    enabled: !!attemptId,
  });
}

/**
 * Hook to start a new test attempt.
 * Returns the attempt with questions (without correct answers).
 */
export function useStartTest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (testId: number) => startTest(testId),
    onSuccess: (data) => {
      // Cache the new attempt
      queryClient.setQueryData(testKeys.attempt(data.id), data);
    },
  });
}

/**
 * Hook to submit test answers.
 * Triggers automatic grading and mastery update on the backend.
 */
export function useSubmitTest(paragraphId?: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ attemptId, answers }: { attemptId: number; answers: AnswerSubmit[] }) =>
      submitTest(attemptId, answers),
    onSuccess: (data, variables) => {
      // Update the cached attempt with results
      queryClient.setQueryData(testKeys.attempt(variables.attemptId), data);

      // Invalidate paragraph test query to update best_score, attempts_count
      if (paragraphId) {
        queryClient.invalidateQueries({ queryKey: testKeys.forParagraph(paragraphId) });
        // Also invalidate paragraph progress as mastery may have changed
        queryClient.invalidateQueries({ queryKey: textbookKeys.paragraphProgress(paragraphId) });
      }

      // Invalidate attempts list
      queryClient.invalidateQueries({ queryKey: testKeys.attempts() });
    },
  });
}

/**
 * Hook to answer a single question in test attempt.
 * Returns immediate feedback with is_correct, correct_option_ids, and explanation.
 * Used for chat-like quiz interface.
 */
export function useAnswerTestQuestion() {
  return useMutation<
    TestAnswerResponse,
    Error,
    { attemptId: number; questionId: number; selectedOptionIds: number[] }
  >({
    mutationFn: ({ attemptId, questionId, selectedOptionIds }) =>
      answerTestQuestion(attemptId, questionId, selectedOptionIds),
  });
}

/**
 * Hook to complete a test attempt after all questions answered via /answer.
 * Triggers grading and mastery update on the backend.
 * Used for chat-like quiz interface.
 */
export function useCompleteTest(paragraphId?: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (attemptId: number) => completeTest(attemptId),
    onSuccess: (data, attemptId) => {
      // Update the cached attempt with results
      queryClient.setQueryData(testKeys.attempt(attemptId), data);

      // Invalidate paragraph test query to update best_score, attempts_count
      if (paragraphId) {
        queryClient.invalidateQueries({ queryKey: testKeys.forParagraph(paragraphId) });
        // Invalidate paragraph progress as mastery may have changed
        queryClient.invalidateQueries({ queryKey: textbookKeys.paragraphProgress(paragraphId) });
      }

      // Invalidate attempts list
      queryClient.invalidateQueries({ queryKey: testKeys.attempts() });
    },
  });
}
