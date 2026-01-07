/**
 * TypeScript types for Homework system.
 * Based on backend schemas from backend/app/schemas/homework.py
 */

// =============================================================================
// Enums
// =============================================================================

export enum HomeworkStatus {
  DRAFT = 'draft',
  PUBLISHED = 'published',
  CLOSED = 'closed',
  ARCHIVED = 'archived',
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

export enum BloomLevel {
  REMEMBER = 'remember',
  UNDERSTAND = 'understand',
  APPLY = 'apply',
  ANALYZE = 'analyze',
  EVALUATE = 'evaluate',
  CREATE = 'create',
}

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

// =============================================================================
// Nested Types
// =============================================================================

export interface QuestionOption {
  id: string;
  text: string;
  is_correct: boolean;
}

export interface RubricCriterion {
  name: string;
  weight: number;
  levels: string[];
  description?: string;
}

export interface GradingRubric {
  criteria: RubricCriterion[];
  max_score: number;
}

export interface GenerationParams {
  questions_count?: number;
  question_types?: QuestionType[];
  bloom_levels?: BloomLevel[];
  include_explanation?: boolean;
  language?: 'ru' | 'kz';
  difficulty?: 'easy' | 'medium' | 'hard';
}

// =============================================================================
// Create/Update Types
// =============================================================================

export interface HomeworkCreate {
  title: string;
  description?: string;
  class_id: number;
  due_date: string; // ISO datetime string

  // AI settings
  ai_generation_enabled?: boolean;
  ai_check_enabled?: boolean;
  target_difficulty?: 'easy' | 'medium' | 'hard' | 'auto';
  personalization_enabled?: boolean;

  // Grading settings
  auto_check_enabled?: boolean;
  show_answers_after?: 'submission' | 'deadline' | 'manual';
  show_explanations?: boolean;

  // Late submission policy
  late_submission_allowed?: boolean;
  late_penalty_per_day?: number;
  grace_period_hours?: number;
  max_late_days?: number;
}

export interface HomeworkUpdate {
  title?: string;
  description?: string;
  due_date?: string;

  ai_generation_enabled?: boolean;
  ai_check_enabled?: boolean;
  target_difficulty?: string;
  personalization_enabled?: boolean;

  auto_check_enabled?: boolean;
  show_answers_after?: string;
  show_explanations?: boolean;

  late_submission_allowed?: boolean;
  late_penalty_per_day?: number;
  grace_period_hours?: number;
  max_late_days?: number;
}

export interface HomeworkTaskCreate {
  paragraph_id?: number;
  chapter_id?: number;
  task_type: TaskType;
  sort_order?: number;
  is_required?: boolean;
  points?: number;
  time_limit_minutes?: number;
  max_attempts?: number;
  instructions?: string;
  ai_prompt_template?: string;
  generation_params?: GenerationParams;
}

export interface QuestionCreate {
  question_text: string;
  question_type: QuestionType;
  options?: QuestionOption[];
  correct_answer?: string;
  answer_pattern?: string;
  points?: number;
  difficulty?: 'easy' | 'medium' | 'hard';
  bloom_level?: BloomLevel;
  explanation?: string;
  grading_rubric?: GradingRubric;
  expected_answer_hints?: string;
  ai_grading_prompt?: string;
}

// =============================================================================
// Response Types
// =============================================================================

export interface QuestionResponse {
  id: number;
  question_text: string;
  question_type: QuestionType;
  options?: QuestionOption[];
  points: number;
  difficulty?: string;
  bloom_level?: BloomLevel;
  explanation?: string;
  version: number;
  is_active: boolean;
  ai_generated: boolean;
  created_at: string;
}

export interface QuestionResponseWithAnswer extends QuestionResponse {
  correct_answer?: string;
  grading_rubric?: GradingRubric;
  expected_answer_hints?: string;
}

export interface HomeworkTaskResponse {
  id: number;
  paragraph_id?: number;
  chapter_id?: number;
  paragraph_title?: string;
  chapter_title?: string;
  task_type: TaskType;
  sort_order: number;
  is_required: boolean;
  points: number;
  time_limit_minutes?: number;
  max_attempts: number;
  ai_generated: boolean;
  instructions?: string;
  questions_count: number;
  questions: QuestionResponse[];
}

export interface HomeworkResponse {
  id: number;
  title: string;
  description?: string;
  status: HomeworkStatus;
  due_date: string;
  class_id: number;
  class_name?: string;
  teacher_id: number;
  teacher_name?: string;

  // AI settings
  ai_generation_enabled: boolean;
  ai_check_enabled: boolean;
  target_difficulty: string;
  personalization_enabled: boolean;

  // Grading settings
  auto_check_enabled: boolean;
  show_answers_after: string;
  show_explanations: boolean;

  // Late policy
  late_submission_allowed: boolean;
  late_penalty_per_day: number;
  grace_period_hours: number;
  max_late_days: number;

  // Computed stats
  total_students: number;
  submitted_count: number;
  graded_count: number;
  average_score?: number;

  tasks: HomeworkTaskResponse[];

  created_at: string;
  updated_at: string;
}

export interface HomeworkListResponse {
  id: number;
  title: string;
  status: HomeworkStatus;
  due_date: string;
  class_id: number;
  class_name?: string;
  tasks_count: number;
  total_students: number;
  submitted_count: number;
  ai_generation_enabled: boolean;
  created_at: string;
}

// =============================================================================
// Review Types
// =============================================================================

export interface AnswerForReview {
  id: number;
  question_id: number;
  question_text: string;
  question_type: QuestionType;
  student_id: number;
  student_name: string;
  answer_text?: string;
  submitted_at: string;
  ai_score?: number;
  ai_confidence?: number;
  ai_feedback?: string;
  grading_rubric?: GradingRubric;
  expected_answer_hints?: string;
}

export interface TeacherReviewRequest {
  score: number;
  feedback?: string;
}

export interface TeacherReviewResponse {
  answer_id: number;
  teacher_score: number;
  teacher_feedback?: string;
  reviewed_at: string;
}

// =============================================================================
// Analytics Types
// =============================================================================

export interface HomeworkAnalytics {
  homework_id: number;
  title: string;
  total_students: number;
  submitted_count: number;
  graded_count: number;
  completion_rate: number;
  average_score?: number;
  min_score?: number;
  max_score?: number;
  median_score?: number;
  average_time_seconds?: number;
  late_submissions: number;
  on_time_submissions: number;
  questions_by_difficulty: Record<string, number>;
  most_missed_questions: Array<{
    question_id: number;
    question_text: string;
    miss_rate: number;
  }>;
  ai_graded_count: number;
  needs_review_count: number;
}

// =============================================================================
// API Query Params
// =============================================================================

export interface HomeworkListParams {
  class_id?: number;
  status?: HomeworkStatus;
  skip?: number;
  limit?: number;
}

export interface ReviewQueueParams {
  homework_id?: number;
  limit?: number;
}
