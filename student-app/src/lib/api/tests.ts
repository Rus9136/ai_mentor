import { apiClient } from './client';

// =============================================================================
// Types - matching backend schemas
// =============================================================================

export type TestPurpose = 'diagnostic' | 'formative' | 'summative' | 'practice';
export type DifficultyLevel = 'easy' | 'medium' | 'hard';
export type QuestionType = 'single_choice' | 'multiple_choice' | 'true_false' | 'short_answer';
export type AttemptStatus = 'in_progress' | 'completed' | 'abandoned';

export interface AvailableTest {
  id: number;
  title: string;
  description: string | null;
  test_purpose: TestPurpose;
  difficulty: DifficultyLevel;
  time_limit: number | null; // in minutes
  passing_score: number; // 0.0 to 1.0
  is_active: boolean;
  chapter_id: number | null;
  paragraph_id: number | null;
  school_id: number | null;
  question_count: number;
  total_points: number;
  attempts_count: number;
  best_score: number | null;
  latest_score: number | null;
  latest_attempt_date: string | null;
  can_retake: boolean;
  created_at: string;
  updated_at: string;
}

export interface QuestionOption {
  id: number;
  question_id: number;
  sort_order: number;
  option_text: string;
  // Note: is_correct is NOT included for security (hidden until submission)
}

export interface QuestionOptionWithAnswer extends QuestionOption {
  is_correct: boolean; // Only available after submission
}

export interface TestQuestion {
  id: number;
  test_id: number;
  sort_order: number;
  question_type: QuestionType;
  question_text: string;
  points: number;
  options: QuestionOption[];
  // Note: explanation is NOT included for security
}

export interface TestQuestionWithAnswer extends Omit<TestQuestion, 'options'> {
  options: QuestionOptionWithAnswer[];
  explanation: string | null; // Only available after submission
}

export interface TestAttemptAnswer {
  id: number;
  attempt_id: number;
  question_id: number;
  selected_option_ids: number[] | null;
  answer_text: string | null;
  is_correct: boolean | null;
  points_earned: number | null;
  answered_at: string;
}

export interface TestAttemptDetail {
  id: number;
  student_id: number;
  test_id: number;
  school_id: number;
  attempt_number: number;
  status: AttemptStatus;
  started_at: string;
  completed_at: string | null;
  score: number | null; // 0.0 to 1.0
  points_earned: number | null;
  total_points: number | null;
  passed: boolean | null;
  time_spent: number | null; // in seconds
  test: {
    id: number;
    title: string;
    description: string | null;
    test_purpose: TestPurpose;
    difficulty: DifficultyLevel;
    time_limit: number | null;
    passing_score: number;
    questions: TestQuestion[] | TestQuestionWithAnswer[];
  };
  answers: TestAttemptAnswer[];
}

export interface AnswerSubmit {
  question_id: number;
  selected_option_ids?: number[];
  answer_text?: string;
}

export interface TestAttemptSubmit {
  answers: AnswerSubmit[];
}

// Single question answer response (for chat-like quiz)
export interface TestAnswerResponse {
  question_id: number;
  is_correct: boolean;
  correct_option_ids: number[];
  explanation: string | null;
  points_earned: number;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Get available tests for a specific paragraph.
 * Returns FORMATIVE tests that student can take after learning the paragraph.
 */
export async function getTestsForParagraph(paragraphId: number): Promise<AvailableTest[]> {
  const response = await apiClient.get<AvailableTest[]>('/students/tests', {
    params: {
      paragraph_id: paragraphId,
      test_purpose: 'formative',
    },
  });
  return response.data;
}

/**
 * Get available tests for a specific chapter.
 * Can filter by test purpose.
 */
export async function getTestsForChapter(
  chapterId: number,
  testPurpose?: TestPurpose
): Promise<AvailableTest[]> {
  const response = await apiClient.get<AvailableTest[]>('/students/tests', {
    params: {
      chapter_id: chapterId,
      ...(testPurpose && { test_purpose: testPurpose }),
    },
  });
  return response.data;
}

/**
 * Start a new test attempt.
 * Creates a TestAttempt with status IN_PROGRESS and returns questions (without correct answers).
 */
export async function startTest(testId: number): Promise<TestAttemptDetail> {
  const response = await apiClient.post<TestAttemptDetail>(`/students/tests/${testId}/start`);
  return response.data;
}

/**
 * Submit all answers for a test attempt.
 * Triggers automatic grading and mastery update.
 * Returns the completed attempt with correct answers revealed.
 */
export async function submitTest(
  attemptId: number,
  answers: AnswerSubmit[]
): Promise<TestAttemptDetail> {
  const response = await apiClient.post<TestAttemptDetail>(
    `/students/attempts/${attemptId}/submit`,
    { answers }
  );
  return response.data;
}

/**
 * Get details of a specific test attempt.
 * If status is COMPLETED, includes correct answers.
 */
export async function getAttempt(attemptId: number): Promise<TestAttemptDetail> {
  const response = await apiClient.get<TestAttemptDetail>(`/students/attempts/${attemptId}`);
  return response.data;
}

/**
 * Get all test attempts for the current student.
 * Can filter by test_id to get history for a specific test.
 */
export async function getStudentAttempts(testId?: number): Promise<TestAttemptDetail[]> {
  const response = await apiClient.get<TestAttemptDetail[]>('/students/attempts', {
    params: testId ? { test_id: testId } : undefined,
  });
  return response.data;
}

/**
 * Submit answer for a single question in test attempt.
 * Returns immediate feedback with is_correct, correct_option_ids, and explanation.
 * Used for chat-like quiz interface.
 */
export async function answerTestQuestion(
  attemptId: number,
  questionId: number,
  selectedOptionIds: number[]
): Promise<TestAnswerResponse> {
  const response = await apiClient.post<TestAnswerResponse>(
    `/students/attempts/${attemptId}/answer`,
    { question_id: questionId, selected_option_ids: selectedOptionIds }
  );
  return response.data;
}

/**
 * Complete a test attempt after all questions have been answered via /answer endpoint.
 * Triggers automatic grading and mastery update.
 * Used for chat-like quiz interface.
 */
export async function completeTest(attemptId: number): Promise<TestAttemptDetail> {
  const response = await apiClient.post<TestAttemptDetail>(
    `/students/attempts/${attemptId}/complete`
  );
  return response.data;
}
