'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useEffect } from 'react';

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
import {
  chapterCreateSchema,
  chapterCreateDefaults,
  type ChapterCreateInput,
  type ChapterUpdateInput,
} from '@/lib/validations/textbook';
import type { Chapter } from '@/types';

interface ChapterDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  textbookId: number;
  chapter?: Chapter;
  nextNumber: number;
  onSubmit: (data: ChapterCreateInput | ChapterUpdateInput) => void;
  isLoading?: boolean;
}

export function ChapterDialog({
  open,
  onOpenChange,
  textbookId,
  chapter,
  nextNumber,
  onSubmit,
  isLoading,
}: ChapterDialogProps) {
  const isEditing = !!chapter;

  const form = useForm<ChapterCreateInput>({
    resolver: zodResolver(chapterCreateSchema),
    defaultValues: chapter
      ? {
          textbook_id: chapter.textbook_id,
          title: chapter.title,
          number: chapter.number,
          order: chapter.order,
          description: chapter.description || '',
          learning_objective: chapter.learning_objective || '',
        }
      : chapterCreateDefaults(textbookId, nextNumber),
  });

  // Reset form when dialog opens/closes or chapter changes
  useEffect(() => {
    if (open) {
      if (chapter) {
        form.reset({
          textbook_id: chapter.textbook_id,
          title: chapter.title,
          number: chapter.number,
          order: chapter.order,
          description: chapter.description || '',
          learning_objective: chapter.learning_objective || '',
        });
      } else {
        form.reset(chapterCreateDefaults(textbookId, nextNumber));
      }
    }
  }, [open, chapter, textbookId, nextNumber, form]);

  const handleSubmit = (data: ChapterCreateInput) => {
    if (isEditing) {
      // For update, exclude textbook_id
      const { textbook_id, ...updateData } = data;
      onSubmit(updateData);
    } else {
      onSubmit(data);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? 'Редактировать главу' : 'Добавить главу'}
          </DialogTitle>
          <DialogDescription>
            {isEditing
              ? 'Измените данные главы'
              : 'Заполните информацию о новой главе'}
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="number"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Номер главы *</FormLabel>
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
                    <Input placeholder="Введение в алгебру" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Описание</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Краткое описание главы..."
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
