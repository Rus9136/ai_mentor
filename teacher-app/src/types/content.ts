/**
 * Content types for teacher textbook/chapter/paragraph browsing.
 * Used by ContentSelector component in homework creation.
 */

export interface SubjectBrief {
  id: number;
  code: string;
  name_ru: string;
  name_kz: string;
}

export interface TextbookListItem {
  id: number;
  school_id: number | null;
  title: string;
  subject_id: number | null;
  subject: string;
  subject_rel: SubjectBrief | null;
  grade_level: number;
  is_customized: boolean;
  is_active: boolean;
  version: number;
  created_at: string;
}

export interface ChapterListItem {
  id: number;
  textbook_id: number;
  title: string;
  number: number;
  order: number;
  created_at: string;
}

export interface ParagraphListItem {
  id: number;
  chapter_id: number;
  title: string;
  number: number;
  order: number;
  summary: string | null;
  key_terms: string[] | null;
  questions: { order: number; text: string }[] | null;
  created_at: string;
}
