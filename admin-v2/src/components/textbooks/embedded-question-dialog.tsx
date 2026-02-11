'use client';

import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useEffect } from 'react';
import { Plus, Trash2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { MathTextarea } from '@/components/ui/math-textarea';
import {
  embeddedQuestionSchema,
  embeddedQuestionDefaults,
  type EmbeddedQuestionInput,
} from '@/lib/validations/embedded-question';
import type { EmbeddedQuestion } from '@/types';

interface EmbeddedQuestionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  question?: EmbeddedQuestion;
  nextOrder: number;
  onSubmit: (data: EmbeddedQuestionInput) => void;
  isLoading?: boolean;
}

const QUESTION_TYPE_LABELS: Record<string, string> = {
  single_choice: 'Один ответ',
  multiple_choice: 'Несколько ответов',
  true_false: 'Верно/Неверно',
};

function nextOptionId(options: { id: string }[]): string {
  const usedIds = new Set(options.map((o) => o.id));
  for (let i = 0; i < 26; i++) {
    const id = String.fromCharCode(97 + i); // a, b, c, ...
    if (!usedIds.has(id)) return id;
  }
  return `opt_${options.length + 1}`;
}

export function EmbeddedQuestionDialog({
  open,
  onOpenChange,
  question,
  nextOrder,
  onSubmit,
  isLoading,
}: EmbeddedQuestionDialogProps) {
  const isEditing = !!question;

  const form = useForm<EmbeddedQuestionInput>({
    resolver: zodResolver(embeddedQuestionSchema),
    defaultValues: embeddedQuestionDefaults(nextOrder),
  });

  const {
    fields: optionFields,
    append: appendOption,
    remove: removeOption,
    replace: replaceOptions,
  } = useFieldArray({
    control: form.control,
    name: 'options',
  });

  const questionType = form.watch('question_type');

  // Reset form when dialog opens/closes or question changes
  useEffect(() => {
    if (open) {
      if (question) {
        form.reset({
          question_text: question.question_text,
          question_type: question.question_type,
          options: question.options || [],
          correct_answer: question.correct_answer || '',
          explanation: question.explanation || '',
          hint: question.hint || '',
          sort_order: question.sort_order,
        });
      } else {
        form.reset(embeddedQuestionDefaults(nextOrder));
      }
    }
  }, [open, question, nextOrder, form]);

  // Auto-fill options for true_false type
  useEffect(() => {
    if (questionType === 'true_false') {
      replaceOptions([
        { id: 'true', text: 'Верно', is_correct: true },
        { id: 'false', text: 'Неверно', is_correct: false },
      ]);
    } else if (
      !isEditing &&
      optionFields.length === 2 &&
      optionFields[0]?.id &&
      form.getValues('options.0.text') === 'Верно'
    ) {
      // Switching away from true_false when creating — reset to defaults
      replaceOptions([
        { id: 'a', text: '', is_correct: true },
        { id: 'b', text: '', is_correct: false },
        { id: 'c', text: '', is_correct: false },
        { id: 'd', text: '', is_correct: false },
      ]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [questionType]);

  const handleSubmit = (data: EmbeddedQuestionInput) => {
    onSubmit(data);
  };

  const isTrueFalse = questionType === 'true_false';

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? 'Редактировать встроенный вопрос' : 'Добавить встроенный вопрос'}
          </DialogTitle>
          <DialogDescription>
            Вопросы &quot;Проверь себя&quot; отображаются внутри параграфа
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="question_type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Тип вопроса *</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Выберите тип" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {Object.entries(QUESTION_TYPE_LABELS).map(([value, label]) => (
                          <SelectItem key={value} value={value}>
                            {label}
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
                name="sort_order"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Порядок</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={0}
                        {...field}
                        onChange={(e) => field.onChange(parseInt(e.target.value) || 0)}
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
                      placeholder="Введите текст вопроса..."
                      minHeight="80px"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Options */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <FormLabel>Варианты ответа *</FormLabel>
                {!isTrueFalse && (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      appendOption({
                        id: nextOptionId(form.getValues('options') || []),
                        text: '',
                        is_correct: false,
                      })
                    }
                  >
                    <Plus className="h-4 w-4 mr-1" />
                    Добавить
                  </Button>
                )}
              </div>

              {optionFields.length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-2">
                  Нет вариантов ответа
                </p>
              )}

              {optionFields.map((field, index) => (
                <div key={field.id} className="flex items-start gap-2">
                  <div className="flex-shrink-0 w-10 pt-2 text-center text-sm font-medium text-muted-foreground">
                    {form.getValues(`options.${index}.id`)}
                  </div>
                  <FormField
                    control={form.control}
                    name={`options.${index}.is_correct`}
                    render={({ field: checkField }) => (
                      <FormItem className="flex-shrink-0 pt-2.5">
                        <FormControl>
                          <Checkbox
                            checked={checkField.value}
                            onCheckedChange={(checked) => {
                              if (questionType === 'single_choice') {
                                // Uncheck all others
                                const options = form.getValues('options') || [];
                                options.forEach((_, i) => {
                                  form.setValue(`options.${i}.is_correct`, i === index);
                                });
                              } else {
                                checkField.onChange(checked);
                              }
                            }}
                            disabled={isTrueFalse}
                          />
                        </FormControl>
                      </FormItem>
                    )}
                  />
                  <div className="flex-1">
                    <FormField
                      control={form.control}
                      name={`options.${index}.text`}
                      render={({ field: textField }) => (
                        <FormItem>
                          <FormControl>
                            <Input
                              placeholder="Текст варианта..."
                              {...textField}
                              disabled={isTrueFalse}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                  {!isTrueFalse && optionFields.length > 2 && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="flex-shrink-0"
                      onClick={() => removeOption(index)}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  )}
                </div>
              ))}
              <FormField
                control={form.control}
                name="options"
                render={() => (
                  <FormItem>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="hint"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Подсказка</FormLabel>
                  <FormControl>
                    <MathTextarea
                      value={field.value || ''}
                      onChange={field.onChange}
                      placeholder="Подсказка для ученика (показывается по запросу)..."
                      minHeight="60px"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="explanation"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Объяснение</FormLabel>
                  <FormControl>
                    <MathTextarea
                      value={field.value || ''}
                      onChange={field.onChange}
                      placeholder="Объяснение правильного ответа (показывается после ответа)..."
                      minHeight="60px"
                    />
                  </FormControl>
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
                {isLoading ? 'Сохранение...' : isEditing ? 'Сохранить' : 'Создать'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
