'use client';

import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useEffect } from 'react';
import { Loader2, Plus, Trash2, HelpCircle } from 'lucide-react';

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
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  paragraphCreateSchema,
  paragraphCreateDefaults,
  type ParagraphCreateInput,
  type ParagraphUpdateInput,
} from '@/lib/validations/textbook';
import type { Paragraph } from '@/types';
import { EmbeddedQuestionsSection } from './embedded-questions-section';

interface ParagraphDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  chapterId: number;
  paragraph?: Paragraph;
  nextNumber: number;
  onSubmit: (data: ParagraphCreateInput | ParagraphUpdateInput) => void;
  isLoading?: boolean;
  isFetchingParagraph?: boolean;
  isSchool?: boolean;
}

export function ParagraphDialog({
  open,
  onOpenChange,
  chapterId,
  paragraph,
  nextNumber,
  onSubmit,
  isLoading,
  isFetchingParagraph,
  isSchool = false,
}: ParagraphDialogProps) {
  const isEditing = !!paragraph;

  const form = useForm<ParagraphCreateInput>({
    resolver: zodResolver(paragraphCreateSchema),
    defaultValues: paragraph
      ? {
          chapter_id: paragraph.chapter_id,
          title: paragraph.title,
          number: paragraph.number,
          order: paragraph.order,
          content: paragraph.content,
          summary: paragraph.summary || '',
          learning_objective: paragraph.learning_objective || '',
          lesson_objective: paragraph.lesson_objective || '',
          key_terms: paragraph.key_terms || [],
          questions: paragraph.questions || [],
        }
      : paragraphCreateDefaults(chapterId, nextNumber),
  });

  const { fields: questionFields, append: appendQuestion, remove: removeQuestion } = useFieldArray({
    control: form.control,
    name: 'questions',
  });

  // Reset form when dialog opens/closes or paragraph changes
  useEffect(() => {
    if (open) {
      if (paragraph) {
        form.reset({
          chapter_id: paragraph.chapter_id,
          title: paragraph.title,
          number: paragraph.number,
          order: paragraph.order,
          content: paragraph.content,
          summary: paragraph.summary || '',
          learning_objective: paragraph.learning_objective || '',
          lesson_objective: paragraph.lesson_objective || '',
          key_terms: paragraph.key_terms || [],
          questions: paragraph.questions || [],
        });
      } else {
        form.reset(paragraphCreateDefaults(chapterId, nextNumber));
      }
    }
  }, [open, paragraph, chapterId, nextNumber, form]);

  const handleSubmit = (data: ParagraphCreateInput) => {
    if (isEditing) {
      // For update, exclude chapter_id
      const { chapter_id, ...updateData } = data;
      onSubmit(updateData);
    } else {
      onSubmit(data);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? 'Редактировать параграф' : 'Добавить параграф'}
          </DialogTitle>
          <DialogDescription>
            {isEditing
              ? 'Измените данные параграфа'
              : 'Заполните информацию о новом параграфе'}
          </DialogDescription>
        </DialogHeader>

        {isFetchingParagraph ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="number"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Номер параграфа *</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={1}
                        {...field}
                        onChange={(e) => field.onChange(parseInt(e.target.value) || 1)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="order"
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
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Название *</FormLabel>
                  <FormControl>
                    <Input placeholder="Линейные уравнения" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="summary"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Краткое содержание</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Краткое описание параграфа..."
                      className="min-h-[60px]"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="content"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Содержание *</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Текст параграфа..."
                      className="min-h-[200px]"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="learning_objective"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Цель обучения</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Что ученик должен узнать..."
                        className="min-h-[80px]"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="lesson_objective"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Цель урока</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Цель конкретного урока..."
                        className="min-h-[80px]"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* Questions Section */}
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center gap-2">
                    <HelpCircle className="h-4 w-4" />
                    Вопросы к параграфу
                  </CardTitle>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => appendQuestion({ order: questionFields.length + 1, text: '' })}
                  >
                    <Plus className="h-4 w-4 mr-1" />
                    Добавить
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {questionFields.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    Нет вопросов. Нажмите &quot;Добавить&quot; для создания вопроса.
                  </p>
                ) : (
                  questionFields.map((field, index) => (
                    <div key={field.id} className="flex gap-2 items-start">
                      <div className="flex-shrink-0 w-12">
                        <FormField
                          control={form.control}
                          name={`questions.${index}.order`}
                          render={({ field }) => (
                            <FormItem>
                              <FormControl>
                                <Input
                                  type="number"
                                  min={1}
                                  className="text-center"
                                  {...field}
                                  onChange={(e) => field.onChange(parseInt(e.target.value) || 1)}
                                />
                              </FormControl>
                            </FormItem>
                          )}
                        />
                      </div>
                      <div className="flex-1">
                        <FormField
                          control={form.control}
                          name={`questions.${index}.text`}
                          render={({ field }) => (
                            <FormItem>
                              <FormControl>
                                <Textarea
                                  placeholder="Текст вопроса..."
                                  className="min-h-[60px]"
                                  {...field}
                                />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="flex-shrink-0"
                        onClick={() => removeQuestion(index)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            {/* Embedded Questions Section (only when editing existing paragraph) */}
            {isEditing && paragraph && (
              <EmbeddedQuestionsSection
                paragraphId={paragraph.id}
                isSchool={isSchool}
              />
            )}

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
        )}
      </DialogContent>
    </Dialog>
  );
}
