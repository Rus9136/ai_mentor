import { z } from 'zod';

// ==================== Textbook ====================

export const textbookCreateSchema = z.object({
  title: z
    .string()
    .min(1, 'Название обязательно')
    .max(255, 'Максимум 255 символов'),
  subject: z
    .string()
    .min(1, 'Предмет обязателен')
    .max(100, 'Максимум 100 символов'),
  grade_level: z
    .number()
    .int()
    .min(1, 'Минимум 1 класс')
    .max(11, 'Максимум 11 класс'),
  author: z.string().max(255, 'Максимум 255 символов').optional().or(z.literal('')),
  publisher: z.string().max(255, 'Максимум 255 символов').optional().or(z.literal('')),
  year: z
    .number()
    .int()
    .min(1900, 'Минимум 1900 год')
    .max(2100, 'Максимум 2100 год')
    .optional(),
  isbn: z.string().max(20, 'Максимум 20 символов').optional().or(z.literal('')),
  description: z.string().optional().or(z.literal('')),
  is_active: z.boolean(),
});

export const textbookUpdateSchema = textbookCreateSchema.partial();

export type TextbookCreateInput = z.infer<typeof textbookCreateSchema>;
export type TextbookUpdateInput = z.infer<typeof textbookUpdateSchema>;

export const textbookCreateDefaults: TextbookCreateInput = {
  title: '',
  subject: '',
  grade_level: 7,
  author: '',
  publisher: '',
  year: new Date().getFullYear(),
  isbn: '',
  description: '',
  is_active: true,
};

// ==================== Chapter ====================

export const chapterCreateSchema = z.object({
  textbook_id: z.number().int().positive('Учебник обязателен'),
  title: z
    .string()
    .min(1, 'Название обязательно')
    .max(255, 'Максимум 255 символов'),
  number: z.number().int().min(1, 'Минимум 1'),
  order: z.number().int().min(0, 'Минимум 0'),
  description: z.string().optional().or(z.literal('')),
  learning_objective: z.string().optional().or(z.literal('')),
});

export const chapterUpdateSchema = chapterCreateSchema.partial().omit({
  textbook_id: true,
});

export type ChapterCreateInput = z.infer<typeof chapterCreateSchema>;
export type ChapterUpdateInput = z.infer<typeof chapterUpdateSchema>;

export const chapterCreateDefaults = (
  textbookId: number,
  nextNumber: number
): ChapterCreateInput => ({
  textbook_id: textbookId,
  title: '',
  number: nextNumber,
  order: nextNumber - 1,
  description: '',
  learning_objective: '',
});

// ==================== Paragraph ====================

export const paragraphCreateSchema = z.object({
  chapter_id: z.number().int().positive('Глава обязательна'),
  title: z
    .string()
    .min(1, 'Название обязательно')
    .max(255, 'Максимум 255 символов'),
  number: z.number().int().min(1, 'Минимум 1'),
  order: z.number().int().min(0, 'Минимум 0'),
  content: z.string().min(1, 'Содержание обязательно'),
  summary: z.string().optional().or(z.literal('')),
  learning_objective: z.string().optional().or(z.literal('')),
  lesson_objective: z.string().optional().or(z.literal('')),
  key_terms: z.array(z.string()).optional(),
});

export const paragraphUpdateSchema = paragraphCreateSchema.partial().omit({
  chapter_id: true,
});

export type ParagraphCreateInput = z.infer<typeof paragraphCreateSchema>;
export type ParagraphUpdateInput = z.infer<typeof paragraphUpdateSchema>;

export const paragraphCreateDefaults = (
  chapterId: number,
  nextNumber: number
): ParagraphCreateInput => ({
  chapter_id: chapterId,
  title: '',
  number: nextNumber,
  order: nextNumber - 1,
  content: '',
  summary: '',
  learning_objective: '',
  lesson_objective: '',
});
