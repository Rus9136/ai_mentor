/**
 * TypeScript types for school gradebook (journal).
 */

export enum GradeType {
  CURRENT = 'CURRENT',
  SOR = 'SOR',
  SOCH = 'SOCH',
  EXAM = 'EXAM',
}

export interface GradeResponse {
  id: number;
  student_id: number;
  school_id: number;
  subject_id: number;
  class_id: number | null;
  teacher_id: number | null;
  created_by: number;
  grade_value: number;
  grade_type: GradeType;
  grade_date: string; // "YYYY-MM-DD"
  quarter: number;
  academic_year: string; // "2025-2026"
  comment: string | null;
  created_at: string;
  updated_at: string;
}

export interface GradeCreate {
  student_id: number;
  subject_id: number;
  class_id?: number;
  grade_value: number; // 1-10
  grade_type: GradeType;
  grade_date: string; // "YYYY-MM-DD"
  quarter: number; // 1-4
  academic_year: string; // "2025-2026"
  comment?: string;
}

export interface GradeUpdate {
  grade_value?: number;
  grade_type?: GradeType;
  grade_date?: string;
  quarter?: number;
  comment?: string;
}

export interface GradeFilterParams {
  quarter?: number;
  academic_year?: string;
  grade_type?: GradeType;
}

export interface SubjectListItem {
  id: number;
  code: string;
  name_ru: string;
  name_kz: string;
  grade_from: number;
  grade_to: number;
  is_active: boolean;
}
