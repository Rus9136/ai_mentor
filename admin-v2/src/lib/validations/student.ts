import { z } from 'zod';

// Schema for creating a new student
export const studentCreateSchema = z.object({
  email: z
    .string()
    .min(1, 'Email обязателен')
    .email('Неверный формат email'),
  password: z
    .string()
    .min(6, 'Минимум 6 символов')
    .max(100, 'Максимум 100 символов'),
  first_name: z
    .string()
    .min(1, 'Имя обязательно')
    .max(100, 'Максимум 100 символов'),
  last_name: z
    .string()
    .min(1, 'Фамилия обязательна')
    .max(100, 'Максимум 100 символов'),
  middle_name: z
    .string()
    .max(100, 'Максимум 100 символов')
    .optional()
    .or(z.literal('')),
  phone: z
    .string()
    .max(50, 'Максимум 50 символов')
    .optional()
    .or(z.literal('')),
  student_code: z
    .string()
    .max(50, 'Максимум 50 символов')
    .optional()
    .or(z.literal('')),
  grade_level: z
    .number()
    .min(1, 'Минимум 1 класс')
    .max(11, 'Максимум 11 класс'),
  birth_date: z
    .string()
    .optional()
    .or(z.literal('')),
  enrollment_date: z
    .string()
    .optional()
    .or(z.literal('')),
});

// Schema for updating a student (without email/password)
export const studentUpdateSchema = z.object({
  first_name: z
    .string()
    .min(1, 'Имя обязательно')
    .max(100, 'Максимум 100 символов')
    .optional(),
  last_name: z
    .string()
    .min(1, 'Фамилия обязательна')
    .max(100, 'Максимум 100 символов')
    .optional(),
  middle_name: z
    .string()
    .max(100, 'Максимум 100 символов')
    .optional()
    .or(z.literal('')),
  phone: z
    .string()
    .max(50, 'Максимум 50 символов')
    .optional()
    .or(z.literal('')),
  student_code: z
    .string()
    .max(50, 'Максимум 50 символов')
    .optional()
    .or(z.literal('')),
  grade_level: z
    .number()
    .min(1, 'Минимум 1 класс')
    .max(11, 'Максимум 11 класс')
    .optional(),
  birth_date: z
    .string()
    .optional()
    .or(z.literal('')),
  enrollment_date: z
    .string()
    .optional()
    .or(z.literal('')),
});

// Infer types from schemas
export type StudentCreateInput = z.infer<typeof studentCreateSchema>;
export type StudentUpdateInput = z.infer<typeof studentUpdateSchema>;

// Default values for forms
export const studentCreateDefaults: StudentCreateInput = {
  email: '',
  password: '',
  first_name: '',
  last_name: '',
  middle_name: '',
  phone: '',
  student_code: '',
  grade_level: 7,
  birth_date: '',
  enrollment_date: '',
};
