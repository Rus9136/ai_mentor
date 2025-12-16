// TypeScript типы для AI Mentor приложения

// Используем const для ролей вместо enum для совместимости с TypeScript настройками
// Значения соответствуют формату в базе данных (lowercase с underscores)
export const UserRole = {
  SUPER_ADMIN: 'super_admin',
  ADMIN: 'admin',
  TEACHER: 'teacher',
  STUDENT: 'student',
  PARENT: 'parent',
} as const;

export type UserRole = typeof UserRole[keyof typeof UserRole];

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
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface School {
  id: number;
  name: string;
  code: string;
  description?: string;
  is_active: boolean;
  email?: string;
  phone?: string;
  address?: string;
  created_at: string;
  updated_at: string;
}

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
  year?: number;
  isbn?: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
  is_deleted: boolean;
}

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

// Типы вопросов для тестов
export const QuestionType = {
  SINGLE_CHOICE: 'single_choice',
  MULTIPLE_CHOICE: 'multiple_choice',
  TRUE_FALSE: 'true_false',
  SHORT_ANSWER: 'short_answer',
} as const;

export type QuestionType = typeof QuestionType[keyof typeof QuestionType];

// Уровни сложности тестов
export const DifficultyLevel = {
  EASY: 'easy',
  MEDIUM: 'medium',
  HARD: 'hard',
} as const;

export type DifficultyLevel = typeof DifficultyLevel[keyof typeof DifficultyLevel];

// Тест
export interface Test {
  id: number;
  school_id: number | null;  // null = глобальный тест
  textbook_id?: number | null;  // Учебник (для каскадного выбора)
  chapter_id?: number | null;
  paragraph_id?: number | null;
  title: string;
  description?: string;
  difficulty: DifficultyLevel;
  time_limit?: number | null;  // минуты
  passing_score: number;  // 0.0-1.0 (например, 0.7 = 70%)
  is_active: boolean;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
  is_deleted: boolean;
}

// Вопрос теста
export interface Question {
  id: number;
  test_id: number;
  sort_order: number;  // Renamed from 'order' to match backend
  question_type: QuestionType;
  question_text: string;
  explanation?: string;  // Объяснение правильного ответа
  points: number;
  options: QuestionOption[];  // Варианты ответов (вложенные)
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
  is_deleted: boolean;
}

// Вариант ответа на вопрос
export interface QuestionOption {
  id: number;
  question_id: number;
  sort_order: number;  // Renamed from 'order' to match backend
  option_text: string;
  is_correct: boolean;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
  is_deleted: boolean;
}

// ==================== USER CRUD ====================
// Request types для User
export interface UserCreate {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  middle_name?: string;
  phone?: string;
  role: UserRole;
}

export interface UserUpdate {
  first_name?: string;
  last_name?: string;
  middle_name?: string;
  phone?: string;
}

// ==================== STUDENT ====================
export interface Student {
  id: number;
  school_id: number;
  user_id: number;
  student_code: string;
  grade_level: number;
  birth_date?: string | null;
  enrollment_date?: string | null;
  user?: User; // Nested user data
  classes?: SchoolClassBrief[]; // Nested classes
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
  is_deleted: boolean;
}

export interface StudentCreate {
  // User fields (транзакционное создание User + Student)
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  middle_name?: string;
  phone?: string;

  // Student fields
  student_code?: string; // Auto-generated если null
  grade_level: number;
  birth_date?: string;
  enrollment_date?: string;
}

export interface StudentUpdate {
  grade_level?: number;
  birth_date?: string;
  enrollment_date?: string;
}

export interface StudentBrief {
  id: number;
  student_code: string;
  grade_level: number;
  user?: {
    first_name: string;
    last_name: string;
    middle_name?: string;
    email?: string;
    phone?: string;
    is_active?: boolean;
  };
}

// ==================== TEACHER ====================
export interface Teacher {
  id: number;
  school_id: number;
  user_id: number;
  teacher_code: string;
  subject?: string | null;
  bio?: string | null;
  hire_date?: string | null;
  user?: User; // Nested user data
  classes?: SchoolClassBrief[]; // Nested classes
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
  is_deleted: boolean;
}

export interface TeacherCreate {
  // User fields (транзакционное создание User + Teacher)
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  middle_name?: string;
  phone?: string;

  // Teacher fields
  teacher_code?: string; // Auto-generated если null
  subject?: string;
  bio?: string;
  hire_date?: string;
}

export interface TeacherUpdate {
  subject?: string;
  bio?: string;
  hire_date?: string;
}

// ==================== PARENT ====================
export interface Parent {
  id: number;
  school_id: number;
  user_id: number;
  user?: User; // Nested user data
  children?: StudentBrief[]; // Nested children (студенты)
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
  is_deleted: boolean;
}

export interface ParentCreate {
  // User fields (транзакционное создание User + Parent)
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  middle_name?: string;
  phone?: string;

  // Parent fields
  student_ids?: number[]; // Initial children
}

// ==================== SCHOOL CLASS ====================
export interface SchoolClass {
  id: number;
  school_id: number;
  name: string;
  code: string;
  grade_level: number;
  academic_year: string;
  students?: Student[]; // Nested students
  teachers?: Teacher[]; // Nested teachers
  students_count?: number; // Calculated field
  teachers_count?: number; // Calculated field
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
  is_deleted: boolean;
}

export interface SchoolClassBrief {
  id: number;
  name: string;
  code: string;
  grade_level: number;
  academic_year?: string;
}

export interface SchoolClassCreate {
  name: string;
  code: string;
  grade_level: number;
  academic_year: string;
}

export interface SchoolClassUpdate {
  name?: string;
  grade_level?: number;
  academic_year?: string;
}

// Bulk operations для классов
export interface AddStudentsRequest {
  student_ids: number[];
}

export interface AddTeachersRequest {
  teacher_ids: number[];
}

// ==================== GOSO (Государственный стандарт образования) ====================

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
  appendix_number?: number;
  amendments?: any[];
  valid_from?: string;
  valid_to?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  deleted_at?: string;
  is_deleted: boolean;
  // Nested
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
  // Nested
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
  // Nested
  outcomes?: LearningOutcome[];
}

export interface LearningOutcome {
  id: number;
  framework_id: number;
  subsection_id: number;
  grade: number;
  code: string;
  title_ru: string;
  title_kz?: string;
  description_ru?: string;
  description_kz?: string;
  cognitive_level?: string;
  display_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  deleted_at?: string;
  is_deleted: boolean;
  // Context (from API)
  section_code?: string;
  section_name_ru?: string;
  subsection_code?: string;
  subsection_name_ru?: string;
}

export interface ParagraphOutcome {
  id: number;
  paragraph_id: number;
  outcome_id: number;
  confidence: number;
  anchor?: string;
  notes?: string;
  created_by?: number;
  created_at: string;
  // Nested details
  outcome_code?: string;
  outcome_title_ru?: string;
  outcome_grade?: number;
}
