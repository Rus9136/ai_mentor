// TypeScript типы для AI Mentor приложения

// Используем const для ролей вместо enum для совместимости с TypeScript настройками
export const UserRole = {
  SUPER_ADMIN: 'SUPER_ADMIN',
  ADMIN: 'ADMIN',
  TEACHER: 'TEACHER',
  STUDENT: 'STUDENT',
  PARENT: 'PARENT',
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
