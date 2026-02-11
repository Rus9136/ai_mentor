import { z } from 'zod';

export const embeddedQuestionOptionSchema = z.object({
  id: z.string().min(1, 'ID обязателен'),
  text: z.string().min(1, 'Текст варианта обязателен'),
  is_correct: z.boolean(),
});

export const embeddedQuestionSchema = z
  .object({
    question_text: z
      .string()
      .min(1, 'Текст вопроса обязателен')
      .max(2000, 'Максимум 2000 символов'),
    question_type: z.enum(['single_choice', 'multiple_choice', 'true_false'], {
      message: 'Выберите тип вопроса',
    }),
    options: z.array(embeddedQuestionOptionSchema).optional(),
    correct_answer: z.string().optional().or(z.literal('')),
    explanation: z.string().optional().or(z.literal('')),
    hint: z.string().optional().or(z.literal('')),
    sort_order: z.number().int().min(0),
  })
  .refine(
    (data) => {
      if (data.question_type === 'true_false') return true;
      return data.options && data.options.length >= 2;
    },
    { message: 'Нужно минимум 2 варианта ответа', path: ['options'] }
  )
  .refine(
    (data) => {
      if (data.question_type === 'true_false') return true;
      return data.options?.some((opt) => opt.is_correct);
    },
    { message: 'Отметьте хотя бы один правильный ответ', path: ['options'] }
  );

export type EmbeddedQuestionInput = z.infer<typeof embeddedQuestionSchema>;

export const embeddedQuestionDefaults = (nextOrder: number): EmbeddedQuestionInput => ({
  question_text: '',
  question_type: 'single_choice',
  options: [
    { id: 'a', text: '', is_correct: true },
    { id: 'b', text: '', is_correct: false },
    { id: 'c', text: '', is_correct: false },
    { id: 'd', text: '', is_correct: false },
  ],
  correct_answer: '',
  explanation: '',
  hint: '',
  sort_order: nextOrder,
});
