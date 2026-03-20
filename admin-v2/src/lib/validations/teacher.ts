import { z } from 'zod';

const KZ_PHONE_RE = /^\+7\d{10}$/;

// Schema for creating a new teacher
export const teacherCreateSchema = z.object({
  email: z
    .string()
    .email('Неверный формат email')
    .optional()
    .or(z.literal('')),
  password: z
    .string()
    .min(8, 'Минимум 8 символов')
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
  teacher_code: z
    .string()
    .max(50, 'Максимум 50 символов')
    .optional()
    .or(z.literal('')),
  subject_id: z
    .number()
    .int()
    .positive()
    .optional()
    .nullable(),
  bio: z
    .string()
    .max(1000, 'Максимум 1000 символов')
    .optional()
    .or(z.literal('')),
}).refine(
  (data) => {
    const hasEmail = !!data.email && data.email.length > 0;
    const hasPhone = !!data.phone && KZ_PHONE_RE.test(data.phone);
    return hasEmail || hasPhone;
  },
  {
    message: 'Укажите email или телефон в формате +7XXXXXXXXXX',
    path: ['phone'],
  }
);

// Schema for updating a teacher (without email/password)
export const teacherUpdateSchema = z.object({
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
  teacher_code: z
    .string()
    .max(50, 'Максимум 50 символов')
    .optional()
    .or(z.literal('')),
  subject_id: z
    .number()
    .int()
    .positive()
    .optional()
    .nullable(),
  bio: z
    .string()
    .max(1000, 'Максимум 1000 символов')
    .optional()
    .or(z.literal('')),
});

// Infer types from schemas
export type TeacherCreateInput = z.infer<typeof teacherCreateSchema>;
export type TeacherUpdateInput = z.infer<typeof teacherUpdateSchema>;

// Default values for forms
export const teacherCreateDefaults: TeacherCreateInput = {
  email: '',
  password: '',
  first_name: '',
  last_name: '',
  middle_name: '',
  phone: '',
  teacher_code: '',
  subject_id: null,
  bio: '',
};
