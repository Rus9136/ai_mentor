import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getStudentTextbooks,
  getTextbookChapters,
  getChapterParagraphs,
  getParagraphDetail,
  getParagraphRichContent,
  getParagraphNavigation,
  getParagraphProgress,
  updateParagraphStep,
  submitSelfAssessment,
  getEmbeddedQuestions,
  answerEmbeddedQuestion,
  StudentTextbook,
  StudentChapter,
  StudentParagraph,
  ParagraphDetail,
  ParagraphRichContent,
  ParagraphNavigation,
  ParagraphProgress,
  ParagraphStep,
  SelfAssessmentRating,
  EmbeddedQuestion,
  AnswerResult,
} from '@/lib/api/textbooks';

// =============================================================================
// Query Keys Factory
// =============================================================================

export const textbookKeys = {
  all: ['textbooks'] as const,
  list: () => [...textbookKeys.all, 'list'] as const,
  chapters: (textbookId: number) => [...textbookKeys.all, textbookId, 'chapters'] as const,
  paragraphs: (chapterId: number) => ['chapters', chapterId, 'paragraphs'] as const,
  paragraph: (paragraphId: number) => ['paragraphs', paragraphId] as const,
  paragraphContent: (paragraphId: number, language: string) =>
    ['paragraphs', paragraphId, 'content', language] as const,
  paragraphNavigation: (paragraphId: number) =>
    ['paragraphs', paragraphId, 'navigation'] as const,
  paragraphProgress: (paragraphId: number) =>
    ['paragraphs', paragraphId, 'progress'] as const,
  embeddedQuestions: (paragraphId: number) =>
    ['paragraphs', paragraphId, 'embedded-questions'] as const,
};

// =============================================================================
// Hooks
// =============================================================================

/**
 * Hook to get all textbooks for the student.
 */
export function useTextbooks() {
  return useQuery<StudentTextbook[], Error>({
    queryKey: textbookKeys.list(),
    queryFn: getStudentTextbooks,
  });
}

/**
 * Hook to get chapters for a textbook.
 */
export function useTextbookChapters(textbookId: number | undefined) {
  return useQuery<StudentChapter[], Error>({
    queryKey: textbookKeys.chapters(textbookId!),
    queryFn: () => getTextbookChapters(textbookId!),
    enabled: !!textbookId,
  });
}

/**
 * Hook to get paragraphs for a chapter.
 */
export function useChapterParagraphs(chapterId: number | undefined) {
  return useQuery<StudentParagraph[], Error>({
    queryKey: textbookKeys.paragraphs(chapterId!),
    queryFn: () => getChapterParagraphs(chapterId!),
    enabled: !!chapterId,
  });
}

/**
 * Hook to get paragraph detail.
 */
export function useParagraphDetail(paragraphId: number | undefined) {
  return useQuery<ParagraphDetail, Error>({
    queryKey: textbookKeys.paragraph(paragraphId!),
    queryFn: () => getParagraphDetail(paragraphId!),
    enabled: !!paragraphId,
  });
}

/**
 * Hook to get paragraph rich content.
 */
export function useParagraphRichContent(
  paragraphId: number | undefined,
  language: 'ru' | 'kz' = 'ru'
) {
  return useQuery<ParagraphRichContent, Error>({
    queryKey: textbookKeys.paragraphContent(paragraphId!, language),
    queryFn: () => getParagraphRichContent(paragraphId!, language),
    enabled: !!paragraphId,
  });
}

/**
 * Hook to get paragraph navigation context.
 */
export function useParagraphNavigation(paragraphId: number | undefined) {
  return useQuery<ParagraphNavigation, Error>({
    queryKey: textbookKeys.paragraphNavigation(paragraphId!),
    queryFn: () => getParagraphNavigation(paragraphId!),
    enabled: !!paragraphId,
  });
}

// =============================================================================
// Progress & Step Tracking Hooks
// =============================================================================

/**
 * Hook to get paragraph progress with step tracking.
 */
export function useParagraphProgress(paragraphId: number | undefined) {
  return useQuery<ParagraphProgress, Error>({
    queryKey: textbookKeys.paragraphProgress(paragraphId!),
    queryFn: () => getParagraphProgress(paragraphId!),
    enabled: !!paragraphId,
  });
}

/**
 * Hook to update paragraph step.
 */
export function useUpdateParagraphStep(paragraphId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ step, timeSpent }: { step: ParagraphStep; timeSpent?: number }) =>
      updateParagraphStep(paragraphId, step, timeSpent),
    onSuccess: () => {
      // Invalidate progress query to refetch updated data
      queryClient.invalidateQueries({ queryKey: textbookKeys.paragraphProgress(paragraphId) });
    },
  });
}

/**
 * Hook to submit self-assessment.
 */
export function useSubmitSelfAssessment(paragraphId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (rating: SelfAssessmentRating) => submitSelfAssessment(paragraphId, rating),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: textbookKeys.paragraphProgress(paragraphId) });
    },
  });
}

// =============================================================================
// Embedded Questions Hooks
// =============================================================================

/**
 * Hook to get embedded questions for a paragraph.
 */
export function useEmbeddedQuestions(paragraphId: number | undefined) {
  return useQuery<EmbeddedQuestion[], Error>({
    queryKey: textbookKeys.embeddedQuestions(paragraphId!),
    queryFn: () => getEmbeddedQuestions(paragraphId!),
    enabled: !!paragraphId,
  });
}

/**
 * Hook to answer an embedded question.
 */
export function useAnswerEmbeddedQuestion(paragraphId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ questionId, answer }: { questionId: number; answer: string | string[] }) =>
      answerEmbeddedQuestion(questionId, answer),
    onSuccess: () => {
      // Invalidate progress to update question stats
      queryClient.invalidateQueries({ queryKey: textbookKeys.paragraphProgress(paragraphId) });
    },
  });
}
