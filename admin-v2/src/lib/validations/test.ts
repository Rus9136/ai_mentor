import { z } from 'zod';

// ==================== Test ====================

export const testCreateSchema = z.object({
  title: z
    .string()
    .min(1, 'Название обязательно')
    .max(255, 'Максимум 255 символов'),
  description: z.string().optional().or(z.literal('')),
  textbook_id: z.number().int().positive('Выберите учебник'),
  chapter_id: z.number().int().positive().optional().nullable(),
  paragraph_id: z.number().int().positive().optional().nullable(),
  test_purpose: z.enum(['diagnostic', 'formative', 'summative', 'practice'], {
    required_error: 'Выберите назначение теста',
  }),
  difficulty: z.enum(['easy', 'medium', 'hard'], {
    required_error: 'Выберите сложность',
  }),
  time_limit: z.number().int().min(1).max(180).optional(),
  passing_score: z
    .number()
    .int()
    .min(0, 'Минимум 0%')
    .max(100, 'Максимум 100%'),
  is_active: z.boolean(),
});

export const testUpdateSchema = testCreateSchema.partial();

export type TestCreateInput = z.infer<typeof testCreateSchema>;
export type TestUpdateInput = z.infer<typeof testUpdateSchema>;

export const testCreateDefaults: TestCreateInput = {
  title: '',
  description: '',
  textbook_id: 0,
  chapter_id: undefined,
  paragraph_id: undefined,
  test_purpose: 'practice',
  difficulty: 'medium',
  time_limit: 30,
  passing_score: 60,
  is_active: true,
};

// ==================== Question ====================

export const questionOptionSchema = z.object({
  sort_order: z.number().int().min(1),
  option_text: z.string().min(1, 'Текст варианта обязателен'),
  is_correct: z.boolean(),
});

export const questionCreateSchema = z.object({
  sort_order: z.number().int().min(1),
  question_type: z.enum(['single_choice', 'multiple_choice', 'true_false', 'short_answer'], {
    required_error: 'Выберите тип вопроса',
  }),
  question_text: z
    .string()
    .min(1, 'Текст вопроса обязателен')
    .max(2000, 'Максимум 2000 символов'),
  explanation: z.string().optional().or(z.literal('')),
  points: z.number().int().min(1, 'Минимум 1 балл').max(100, 'Максимум 100 баллов'),
  options: z.array(questionOptionSchema).optional(),
});

export const questionUpdateSchema = questionCreateSchema.partial();

export type QuestionOptionInput = z.infer<typeof questionOptionSchema>;
export type QuestionCreateInput = z.infer<typeof questionCreateSchema>;
export type QuestionUpdateInput = z.infer<typeof questionUpdateSchema>;

export const questionCreateDefaults = (nextOrder: number): QuestionCreateInput => ({
  sort_order: nextOrder + 1, // Backend expects sort_order >= 1
  question_type: 'single_choice',
  question_text: '',
  explanation: '',
  points: 1,
  options: [
    { sort_order: 1, option_text: '', is_correct: true },
    { sort_order: 2, option_text: '', is_correct: false },
    { sort_order: 3, option_text: '', is_correct: false },
    { sort_order: 4, option_text: '', is_correct: false },
  ],
});
