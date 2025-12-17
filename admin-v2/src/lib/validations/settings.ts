import { z } from 'zod';

// Schema for updating school settings
export const settingsUpdateSchema = z.object({
  name: z
    .string()
    .min(1, 'Название обязательно')
    .max(255, 'Максимум 255 символов')
    .optional(),
  description: z
    .string()
    .max(1000, 'Максимум 1000 символов')
    .optional()
    .or(z.literal('')),
  email: z
    .string()
    .email('Неверный формат email')
    .optional()
    .or(z.literal('')),
  phone: z
    .string()
    .max(50, 'Максимум 50 символов')
    .optional()
    .or(z.literal('')),
  address: z
    .string()
    .max(500, 'Максимум 500 символов')
    .optional()
    .or(z.literal('')),
});

// Infer types from schemas
export type SettingsUpdateInput = z.infer<typeof settingsUpdateSchema>;

// Default values for forms
export const settingsUpdateDefaults: SettingsUpdateInput = {
  name: '',
  description: '',
  email: '',
  phone: '',
  address: '',
};
