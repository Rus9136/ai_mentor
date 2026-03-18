// Test types (mirrors admin-v2 types)
export type DifficultyLevel = 'easy' | 'medium' | 'hard';
export type TestPurpose = 'diagnostic' | 'formative' | 'summative' | 'practice';
export type QuestionType = 'single_choice' | 'multiple_choice' | 'true_false' | 'short_answer';

export interface Test {
  id: number;
  school_id: number | null;
  textbook_id?: number | null;
  chapter_id?: number | null;
  paragraph_id?: number | null;
  title: string;
  description?: string;
  test_purpose: TestPurpose;
  difficulty: DifficultyLevel;
  time_limit?: number | null;
  passing_score: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  deleted_at?: string | null;
  is_deleted?: boolean;
  textbook_title?: string | null;
  chapter_title?: string | null;
  paragraph_title?: string | null;
  grade_level?: number | null;
}

export interface TestCreate {
  title: string;
  description?: string;
  textbook_id: number;
  chapter_id?: number | null;
  paragraph_id?: number | null;
  test_purpose: TestPurpose;
  difficulty: DifficultyLevel;
  time_limit?: number;
  passing_score: number;
  is_active?: boolean;
}

export interface TestUpdate extends Partial<TestCreate> {}

export interface QuestionOption {
  id: number;
  question_id: number;
  sort_order: number;
  option_text: string;
  is_correct: boolean;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
  is_deleted: boolean;
}

export interface QuestionOptionCreate {
  sort_order: number;
  option_text: string;
  is_correct: boolean;
}

export interface QuestionOptionUpdate extends Partial<QuestionOptionCreate> {}

export interface Question {
  id: number;
  test_id: number;
  sort_order: number;
  question_type: QuestionType;
  question_text: string;
  explanation?: string;
  points: number;
  options: QuestionOption[];
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
  is_deleted: boolean;
}

export interface QuestionCreate {
  sort_order: number;
  question_type: QuestionType;
  question_text: string;
  explanation?: string;
  points: number;
  options?: QuestionOptionCreate[];
}

export interface QuestionUpdate extends Partial<QuestionCreate> {}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
