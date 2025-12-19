// User & Auth types
export type UserRole = 'super_admin' | 'admin' | 'teacher' | 'student' | 'parent';

export interface User {
  id: number;
  email: string;
  role: UserRole;
  school_id: number | null;
  first_name?: string;
  last_name?: string;
  middle_name?: string;
  phone?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// School types
export interface School {
  id: number;
  name: string;
  code: string;
  description?: string;
  email?: string;
  phone?: string;
  address?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SchoolCreate {
  name: string;
  code: string;
  description?: string;
  email?: string;
  phone?: string;
  address?: string;
}

export interface SchoolUpdate extends Partial<SchoolCreate> {}

// Textbook types
export interface Textbook {
  id: number;
  school_id: number | null;
  global_textbook_id?: number | null;
  is_customized: boolean;
  version: number;
  source_version?: number | null;
  title: string;
  subject: string;
  grade_level: number;
  author?: string;
  publisher?: string;
  isbn?: string;
  description?: string;
  year?: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
  is_deleted: boolean;
}

export interface TextbookCreate {
  title: string;
  subject: string;
  grade_level: number;
  author?: string;
  publisher?: string;
  year?: number;
  isbn?: string;
  description?: string;
  is_active?: boolean;
}

export interface TextbookUpdate extends Partial<TextbookCreate> {}

// Chapter types
export interface Chapter {
  id: number;
  textbook_id: number;
  title: string;
  number: number;
  order: number;
  description?: string;
  learning_objective?: string;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
  is_deleted: boolean;
}

export interface ChapterCreate {
  textbook_id: number;
  title: string;
  number: number;
  order: number;
  description?: string;
  learning_objective?: string;
}

export interface ChapterUpdate extends Partial<Omit<ChapterCreate, 'textbook_id'>> {}

// Paragraph types
export interface ParagraphQuestion {
  order: number;
  text: string;
}

export interface Paragraph {
  id: number;
  chapter_id: number;
  title: string;
  number: number;
  order: number;
  content: string;
  summary?: string;
  learning_objective?: string;
  lesson_objective?: string;
  key_terms?: string[];
  questions?: ParagraphQuestion[];
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
  is_deleted: boolean;
}

export interface ParagraphCreate {
  chapter_id: number;
  title: string;
  number: number;
  order: number;
  content: string;
  summary?: string;
  learning_objective?: string;
  lesson_objective?: string;
  key_terms?: string[];
  questions?: ParagraphQuestion[];
}

export interface ParagraphUpdate extends Partial<Omit<ParagraphCreate, 'chapter_id'>> {}

// Test types
export type DifficultyLevel = 'easy' | 'medium' | 'hard';
export type TestPurpose = 'diagnostic' | 'formative' | 'summative' | 'practice';

export interface Test {
  id: number;
  school_id: number | null;
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
  updated_at: string;
  deleted_at?: string | null;
  is_deleted: boolean;
}

export interface TestCreate {
  title: string;
  description?: string;
  chapter_id?: number;
  paragraph_id?: number;
  test_purpose: TestPurpose;
  difficulty: DifficultyLevel;
  time_limit?: number;
  passing_score: number;
  is_active?: boolean;
}

export interface TestUpdate extends Partial<TestCreate> {}

// Question types
export type QuestionType = 'single_choice' | 'multiple_choice' | 'true_false' | 'short_answer';

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

// Student types
export interface Student {
  id: number;
  school_id: number;
  user_id: number;
  student_code: string;
  grade_level: number;
  birth_date?: string | null;
  enrollment_date?: string | null;
  user?: User;
  classes?: SchoolClassBrief[];
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
  is_deleted: boolean;
}

export interface StudentCreate {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  middle_name?: string;
  phone?: string;
  student_code?: string;
  grade_level: number;
  birth_date?: string;
  enrollment_date?: string;
}

export interface StudentUpdate extends Partial<Omit<StudentCreate, 'email' | 'password'>> {}

// Teacher types
export interface Teacher {
  id: number;
  school_id: number;
  user_id: number;
  teacher_code: string;
  subject?: string | null;
  bio?: string | null;
  user?: User;
  classes?: SchoolClassBrief[];
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
  is_deleted: boolean;
}

export interface TeacherCreate {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  middle_name?: string;
  phone?: string;
  teacher_code?: string;
  subject?: string;
  bio?: string;
}

export interface TeacherUpdate extends Partial<Omit<TeacherCreate, 'email' | 'password'>> {}

// Parent types
export interface Parent {
  id: number;
  school_id: number;
  user_id: number;
  user?: User;
  children?: Student[];
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
  is_deleted: boolean;
}

export interface ParentCreate {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  middle_name?: string;
  phone?: string;
  child_ids?: number[];
}

// Class types
export interface SchoolClassBrief {
  id: number;
  name: string;
  code: string;
  grade_level: number;
  academic_year?: string;
}

export interface SchoolClass {
  id: number;
  school_id: number;
  name: string;
  code: string;
  grade_level: number;
  academic_year: string;
  students?: Student[];
  teachers?: Teacher[];
  students_count?: number;
  teachers_count?: number;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
  is_deleted: boolean;
}

export interface SchoolClassCreate {
  name: string;
  code: string;
  grade_level: number;
  academic_year: string;
}

export interface SchoolClassUpdate extends Partial<SchoolClassCreate> {}

// GOSO types
export interface Subject {
  id: number;
  code: string;
  name_ru: string;
  name_kz: string;
  description_ru?: string;
  description_kz?: string;
  grade_from: number;
  grade_to: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Framework {
  id: number;
  code: string;
  subject_id: number;
  title_ru: string;
  title_kz?: string;
  description_ru?: string;
  description_kz?: string;
  document_type?: string;
  order_number?: string;
  order_date?: string;
  ministry?: string;
  valid_from?: string;
  valid_to?: string;
  amendments?: unknown[];
  appendix_number?: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  deleted_at?: string;
  is_deleted: boolean;
  subject?: Subject;
  sections?: GosoSection[];
}

export interface GosoSection {
  id: number;
  framework_id: number;
  code: string;
  name_ru: string;
  name_kz?: string;
  description_ru?: string;
  description_kz?: string;
  display_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  subsections?: GosoSubsection[];
}

export interface GosoSubsection {
  id: number;
  section_id: number;
  code: string;
  name_ru: string;
  name_kz?: string;
  description_ru?: string;
  description_kz?: string;
  display_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  outcomes?: LearningOutcome[];
}

export interface LearningOutcome {
  id: number;
  framework_id: number;
  subsection_id: number;
  grade: number;
  code: string;
  title_ru: string;
  title_kk?: string;
  description_ru?: string;
  description_kk?: string;
  cognitive_level?: string;
  display_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  deleted_at?: string;
  is_deleted: boolean;
  section_code?: string;
  section_name_ru?: string;
  subsection_code?: string;
  subsection_name_ru?: string;
}

// Paragraph Content types
export type ContentStatus = 'empty' | 'draft' | 'ready' | 'outdated';
export type CardType = 'term' | 'fact' | 'check';

export interface CardItem {
  id: string;
  type: CardType;
  front: string;
  back: string;
  order: number;
}

export interface ParagraphContent {
  id: number;
  paragraph_id: number;
  language: 'ru' | 'kz';
  explain_text: string | null;
  audio_url: string | null;
  slides_url: string | null;
  video_url: string | null;
  cards: CardItem[] | null;
  source_hash: string | null;
  status_explain: ContentStatus;
  status_audio: ContentStatus;
  status_slides: ContentStatus;
  status_video: ContentStatus;
  status_cards: ContentStatus;
  created_at: string;
  updated_at: string;
}

export interface ParagraphContentUpdate {
  explain_text?: string | null;
}

export interface ParagraphContentCardsUpdate {
  cards: CardItem[];
}

// API types
export interface ApiError {
  detail: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}
