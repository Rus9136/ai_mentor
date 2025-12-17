import { z } from 'zod';

// Schema for creating a new school
export const schoolCreateSchema = z.object({
  name: z
    .string()
    .min(1, 'Название обязательно')
    .max(255, 'Максимум 255 символов'),
  code: z
    .string()
    .min(2, 'Минимум 2 символа')
    .max(50, 'Максимум 50 символов')
    .regex(
      /^[a-z0-9_-]+$/,
      'Только lowercase буквы, цифры, дефисы и underscores'
    ),
  email: z
    .string()
    .email('Неверный формат email')
    .optional()
    .or(z.literal('')),
  phone: z.string().max(50, 'Максимум 50 символов').optional().or(z.literal('')),
  address: z.string().optional().or(z.literal('')),
  description: z.string().optional().or(z.literal('')),
});

// Schema for updating a school (all fields optional)
export const schoolUpdateSchema = schoolCreateSchema.partial();

// Infer types from schemas
export type SchoolCreateInput = z.infer<typeof schoolCreateSchema>;
export type SchoolUpdateInput = z.infer<typeof schoolUpdateSchema>;

// Default values for forms
export const schoolCreateDefaults: SchoolCreateInput = {
  name: '',
  code: '',
  email: '',
  phone: '',
  address: '',
  description: '',
};
