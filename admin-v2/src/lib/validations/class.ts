import { z } from 'zod';

// Schema for creating a new class
export const classCreateSchema = z.object({
  name: z
    .string()
    .min(1, 'Название обязательно')
    .max(50, 'Максимум 50 символов'),
  code: z
    .string()
    .min(1, 'Код обязателен')
    .max(20, 'Максимум 20 символов'),
  grade_level: z
    .number()
    .min(1, 'Минимум 1 класс')
    .max(11, 'Максимум 11 класс'),
  academic_year: z
    .string()
    .min(1, 'Учебный год обязателен')
    .regex(/^\d{4}-\d{4}$/, 'Формат: 2024-2025'),
});

// Schema for updating a class
export const classUpdateSchema = classCreateSchema.partial();

// Infer types from schemas
export type ClassCreateInput = z.infer<typeof classCreateSchema>;
export type ClassUpdateInput = z.infer<typeof classUpdateSchema>;

// Default values for forms
export const classCreateDefaults: ClassCreateInput = {
  name: '',
  code: '',
  grade_level: 7,
  academic_year: `${new Date().getFullYear()}-${new Date().getFullYear() + 1}`,
};
