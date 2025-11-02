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
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
  is_deleted: boolean;
}
