import { z } from 'zod';

// Schema for creating a new parent
export const parentCreateSchema = z.object({
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
  child_ids: z
    .array(z.number())
    .optional(),
});

// Infer types from schemas
export type ParentCreateInput = z.infer<typeof parentCreateSchema>;

// Default values for forms
export const parentCreateDefaults: ParentCreateInput = {
  email: '',
  password: '',
  first_name: '',
  last_name: '',
  middle_name: '',
  phone: '',
  child_ids: [],
};
