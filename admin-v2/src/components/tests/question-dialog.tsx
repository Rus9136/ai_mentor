'use client';

import { useEffect } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Plus, Trash2, GripVertical } from 'lucide-react';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { MathTextarea } from '@/components/ui/math-textarea';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  questionCreateSchema,
  questionCreateDefaults,
  type QuestionCreateInput,
} from '@/lib/validations/test';
import type { Question, QuestionType } from '@/types';

interface QuestionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  question?: Question;
  nextOrder: number;
  onSubmit: (data: QuestionCreateInput) => void;
  isLoading?: boolean;
}

const QUESTION_TYPES = [
  { value: 'single_choice', label: 'Один правильный ответ' },
  { value: 'multiple_choice', label: 'Несколько правильных ответов' },
  { value: 'true_false', label: 'Верно / Неверно' },
  { value: 'short_answer', label: 'Краткий ответ' },
] as const;

export function QuestionDialog({
  open,
  onOpenChange,
  question,
  nextOrder,
  onSubmit,
  isLoading,
}: QuestionDialogProps) {
  const isEdit = !!question;

  const form = useForm<QuestionCreateInput>({
    resolver: zodResolver(questionCreateSchema),
    defaultValues: questionCreateDefaults(nextOrder),
  });

  const { fields, append, remove, move } = useFieldArray({
    control: form.control,
    name: 'options',
  });

  const questionType = form.watch('question_type');

  // Reset form when dialog opens/closes or question changes
  useEffect(() => {
    if (open) {
      if (question) {
        form.reset({
          sort_order: question.sort_order,
          question_type: question.question_type,
          question_text: question.question_text,
          explanation: question.explanation || '',
          points: question.points,
          options: question.options.map((o) => ({
            sort_order: o.sort_order,
            option_text: o.option_text,
            is_correct: o.is_correct,
          })),
        });
      } else {
        form.reset(questionCreateDefaults(nextOrder));
      }
    }
  }, [open, question, nextOrder, form]);

  // Handle true/false type - set predefined options
  useEffect(() => {
    if (questionType === 'true_false' && !isEdit) {
      form.setValue('options', [
        { sort_order: 1, option_text: 'Верно', is_correct: true },
        { sort_order: 2, option_text: 'Неверно', is_correct: false },
      ]);
    }
  }, [questionType, form, isEdit]);

  const handleSubmit = (data: QuestionCreateInput) => {
    onSubmit(data);
  };

  const addOption = () => {
    append({
      sort_order: fields.length + 1, // Backend expects sort_order >= 1
      option_text: '',
      is_correct: false,
    });
  };

  const showOptions = questionType !== 'short_answer';

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? 'Редактировать вопрос' : 'Добавить вопрос'}
          </DialogTitle>
          <DialogDescription>
            {isEdit
              ? 'Измените параметры вопроса'
              : 'Заполните информацию о новом вопросе'}
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2">
              <FormField
                control={form.control}
                name="question_type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Тип вопроса *</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      defaultValue={field.value}
                      value={field.value}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Выберите тип" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {QUESTION_TYPES.map((type) => (
                          <SelectItem key={type.value} value={type.value}>
                            {type.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="points"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Баллы *</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={1}
                        max={100}
                        {...field}
                        onChange={(e) => field.onChange(parseInt(e.target.value) || 1)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="question_text"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Текст вопроса *</FormLabel>
                  <FormControl>
                    <MathTextarea
                      value={field.value}
                      onChange={field.onChange}
                      placeholder="Введите текст вопроса... Для формул используйте $формула$"
                      minHeight="100px"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {showOptions && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <FormLabel>Варианты ответов</FormLabel>
                  {questionType !== 'true_false' && (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={addOption}
                    >
                      <Plus className="mr-2 h-4 w-4" />
                      Добавить вариант
                    </Button>
                  )}
                </div>

                <div className="space-y-3">
                  {fields.map((field, index) => (
                    <div
                      key={field.id}
                      className="flex items-start gap-3 rounded-lg border p-3"
                    >
                      <div className="flex items-center gap-2 pt-2">
                        <FormField
                          control={form.control}
                          name={`options.${index}.is_correct`}
                          render={({ field }) => (
                            <FormItem>
                              <FormControl>
                                <Checkbox
                                  checked={field.value}
                                  onCheckedChange={field.onChange}
                                />
                              </FormControl>
                            </FormItem>
                          )}
                        />
                      </div>

                      <div className="flex-1 space-y-2">
                        <FormField
                          control={form.control}
                          name={`options.${index}.option_text`}
                          render={({ field }) => (
                            <FormItem>
                              <FormControl>
                                <Input
                                  placeholder={`Вариант ${index + 1} (для формул: $x^2$)`}
                                  {...field}
                                  disabled={questionType === 'true_false'}
                                />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                      </div>

                      {questionType !== 'true_false' && fields.length > 2 && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={() => remove(index)}
                          className="text-destructive hover:text-destructive"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>

                <FormDescription>
                  Отметьте галочкой правильные варианты ответа. Для формул используйте $формула$.
                </FormDescription>
              </div>
            )}

            <FormField
              control={form.control}
              name="explanation"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Пояснение (необязательно)</FormLabel>
                  <FormControl>
                    <MathTextarea
                      value={field.value || ''}
                      onChange={field.onChange}
                      placeholder="Пояснение к правильному ответу... Можно использовать формулы."
                      minHeight="80px"
                    />
                  </FormControl>
                  <FormDescription>
                    Будет показано ученику после ответа на вопрос
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                Отмена
              </Button>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? 'Сохранение...' : isEdit ? 'Сохранить' : 'Добавить'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
