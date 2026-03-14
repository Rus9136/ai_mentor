import { z } from 'zod';

// Admin credentials schema (used when creating admin with school)
const adminCredentialsSchema = z.object({
  email: z.string().email('Неверный формат email'),
  password: z.string().min(6, 'Минимум 6 символов'),
  first_name: z.string().min(1, 'Имя обязательно').max(100),
  last_name: z.string().min(1, 'Фамилия обязательна').max(100),
  middle_name: z.string().max(100).optional().or(z.literal('')),
});

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
  create_admin: z.boolean().optional(),
  admin: adminCredentialsSchema.optional(),
}).superRefine((data, ctx) => {
  if (data.create_admin && !data.admin) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: 'Заполните данные администратора',
      path: ['admin'],
    });
  }
  if (data.create_admin && data.admin) {
    // Validate admin fields are filled
    if (!data.admin.email) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Email обязателен',
        path: ['admin', 'email'],
      });
    }
    if (!data.admin.password || data.admin.password.length < 6) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Минимум 6 символов',
        path: ['admin', 'password'],
      });
    }
    if (!data.admin.first_name) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Имя обязательно',
        path: ['admin', 'first_name'],
      });
    }
    if (!data.admin.last_name) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Фамилия обязательна',
        path: ['admin', 'last_name'],
      });
    }
  }
});

// Schema for password reset
export const adminPasswordResetSchema = z.object({
  password: z.string().min(6, 'Минимум 6 символов'),
});

// Schema for updating a school (all fields optional, no admin)
export const schoolUpdateSchema = z.object({
  name: z
    .string()
    .min(1, 'Название обязательно')
    .max(255, 'Максимум 255 символов')
    .optional(),
  code: z
    .string()
    .min(2, 'Минимум 2 символа')
    .max(50, 'Максимум 50 символов')
    .regex(
      /^[a-z0-9_-]+$/,
      'Только lowercase буквы, цифры, дефисы и underscores'
    )
    .optional(),
  email: z
    .string()
    .email('Неверный формат email')
    .optional()
    .or(z.literal('')),
  phone: z.string().max(50, 'Максимум 50 символов').optional().or(z.literal('')),
  address: z.string().optional().or(z.literal('')),
  description: z.string().optional().or(z.literal('')),
}).partial();

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
  create_admin: false,
  admin: {
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    middle_name: '',
  },
};
