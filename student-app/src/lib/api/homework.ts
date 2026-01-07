/**
 * Student Homework API
 *
 * API functions and types for student homework system.
 */

import { apiClient } from './client';

// =============================================================================
// Pagination Type
// =============================================================================

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// =============================================================================
// Enums
// =============================================================================

export enum StudentHomeworkStatus {
  ASSIGNED = 'assigned',
  IN_PROGRESS = 'in_progress',
  SUBMITTED = 'submitted',
  GRADED = 'graded',
  RETURNED = 'returned',
}

export enum SubmissionStatus {
  NOT_STARTED = 'not_started',
  IN_PROGRESS = 'in_progress',
  SUBMITTED = 'submitted',
  GRADED = 'graded',
}

export enum TaskType {
  READ = 'read',
  QUIZ = 'quiz',
  OPEN_QUESTION = 'open_question',
  ESSAY = 'essay',
  PRACTICE = 'practice',
  CODE = 'code',
}

export enum QuestionType {
  SINGLE_CHOICE = 'single_choice',
  MULTIPLE_CHOICE = 'multiple_choice',
  TRUE_FALSE = 'true_false',
  SHORT_ANSWER = 'short_answer',
  OPEN_ENDED = 'open_ended',
  CODE = 'code',
}

// =============================================================================
// Response Types
// =============================================================================

export interface QuestionOption {
  id: string;
  text: string;
  // Note: is_correct is NOT included for student view
}

export interface StudentQuestionResponse {
  id: number;
  question_text: string;
  question_type: QuestionType;
  options: QuestionOption[] | null;
  points: number;
  my_answer: string | null;
  my_selected_options: string[] | null;
  is_answered: boolean;
}

export interface StudentQuestionWithFeedback extends StudentQuestionResponse {
  is_correct: boolean | null;
  score: number | null;
  max_score: number;
  explanation: string | null;
  ai_feedback: string | null;
  ai_confidence: number | null;
}

export interface StudentTaskResponse {
  id: number;
  paragraph_id: number | null;
  paragraph_title: string | null;
  task_type: TaskType;
  instructions: string | null;
  points: number;
  time_limit_minutes: number | null;
  status: SubmissionStatus;
  current_attempt: number;
  max_attempts: number;
  attempts_remaining: number;
  my_score: number | null;
  questions_count: number;
  answered_count: number;
  submission_id?: number | null;
}

export interface StudentHomeworkResponse {
  id: number;
  title: string;
  description: string | null;
  due_date: string;
  is_overdue: boolean;
  can_submit: boolean;
  my_status: StudentHomeworkStatus;
  my_score: number | null;
  max_score: number;
  my_percentage: number | null;
  is_late: boolean;
  late_penalty: number;
  show_explanations: boolean;
  tasks: StudentTaskResponse[];
}

// =============================================================================
// Submit Types
// =============================================================================

export interface AnswerSubmit {
  question_id: number;
  answer_text?: string;
  selected_options?: string[];
}

export interface SubmissionResult {
  submission_id: number;
  question_id: number;
  is_correct: boolean | null;
  score: number;
  max_score: number;
  feedback: string | null;
  explanation: string | null;
  ai_feedback: string | null;
  ai_confidence: number | null;
  needs_review: boolean;
}

export interface TaskSubmissionResult {
  submission_id: number;
  task_id: number;
  status: SubmissionStatus;
  attempt_number: number;
  total_score: number;
  max_score: number;
  percentage: number;
  is_late: boolean;
  late_penalty_applied: number;
  original_score: number | null;
  answers: SubmissionResult[];
  correct_count: number;
  incorrect_count: number;
  needs_review_count: number;
}

// =============================================================================
// Query Params
// =============================================================================

export interface HomeworkListParams {
  status?: StudentHomeworkStatus;
  include_completed?: boolean;
}

// =============================================================================
// API Functions - Homework List
// =============================================================================

export async function listMyHomework(
  params?: HomeworkListParams
): Promise<StudentHomeworkResponse[]> {
  const response = await apiClient.get<PaginatedResponse<StudentHomeworkResponse>>(
    '/students/homework',
    { params }
  );
  return response.data.items;
}

export async function getHomeworkDetail(
  homeworkId: number
): Promise<StudentHomeworkResponse> {
  const response = await apiClient.get<StudentHomeworkResponse>(
    `/students/homework/${homeworkId}`
  );
  return response.data;
}

// =============================================================================
// API Functions - Task Operations
// =============================================================================

export async function startTask(
  homeworkId: number,
  taskId: number
): Promise<StudentTaskResponse> {
  const response = await apiClient.post<StudentTaskResponse>(
    `/students/homework/${homeworkId}/tasks/${taskId}/start`
  );
  return response.data;
}

export async function getTaskQuestions(
  homeworkId: number,
  taskId: number
): Promise<StudentQuestionResponse[]> {
  const response = await apiClient.get<StudentQuestionResponse[]>(
    `/students/homework/${homeworkId}/tasks/${taskId}/questions`
  );
  return response.data;
}

// =============================================================================
// API Functions - Submissions
// =============================================================================

export async function submitAnswer(
  submissionId: number,
  data: AnswerSubmit
): Promise<SubmissionResult> {
  const response = await apiClient.post<SubmissionResult>(
    `/students/homework/submissions/${submissionId}/answer`,
    data
  );
  return response.data;
}

export async function completeSubmission(
  submissionId: number
): Promise<TaskSubmissionResult> {
  const response = await apiClient.post<TaskSubmissionResult>(
    `/students/homework/submissions/${submissionId}/complete`
  );
  return response.data;
}

export async function getSubmissionResults(
  submissionId: number
): Promise<StudentQuestionWithFeedback[]> {
  const response = await apiClient.get<StudentQuestionWithFeedback[]>(
    `/students/homework/submissions/${submissionId}/results`
  );
  return response.data;
}
