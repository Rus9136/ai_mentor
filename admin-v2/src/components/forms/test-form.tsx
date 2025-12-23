'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useTranslations } from 'next-intl';

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
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  testCreateSchema,
  testCreateDefaults,
  type TestCreateInput,
} from '@/lib/validations/test';
import { useTextbooks, useChapters, useParagraphs } from '@/lib/hooks/use-textbooks';
import type { Test } from '@/types';

interface TestFormProps {
  test?: Test;
  onSubmit: (data: TestCreateInput) => void;
  isLoading?: boolean;
  isSchool?: boolean;
}

const TEST_PURPOSES = [
  { value: 'diagnostic', label: 'Диагностический' },
  { value: 'formative', label: 'Формативный' },
  { value: 'summative', label: 'Суммативный' },
  { value: 'practice', label: 'Практический' },
] as const;

const DIFFICULTIES = [
  { value: 'easy', label: 'Легкий' },
  { value: 'medium', label: 'Средний' },
  { value: 'hard', label: 'Сложный' },
] as const;

export function TestForm({ test, onSubmit, isLoading, isSchool = false }: TestFormProps) {
  const t = useTranslations('tests');
  const tCommon = useTranslations('common');

  const form = useForm<TestCreateInput>({
    resolver: zodResolver(testCreateSchema),
    defaultValues: test
      ? {
          title: test.title,
          description: test.description || '',
          textbook_id: test.textbook_id || 0,
          chapter_id: test.chapter_id || undefined,
          paragraph_id: test.paragraph_id || undefined,
          test_purpose: test.test_purpose,
          difficulty: test.difficulty,
          time_limit: test.time_limit || undefined,
          passing_score: test.passing_score,
          is_active: test.is_active,
        }
      : testCreateDefaults,
  });

  // Watch values for cascading selects
  const selectedTextbookId = form.watch('textbook_id');
  const selectedChapterId = form.watch('chapter_id');

  // Fetch textbooks
  const { data: textbooks = [], isLoading: textbooksLoading } = useTextbooks(isSchool);

  // Fetch chapters when textbook is selected
  const { data: chapters = [], isLoading: chaptersLoading } = useChapters(
    selectedTextbookId,
    isSchool,
    selectedTextbookId > 0
  );

  // Fetch paragraphs when chapter is selected
  const { data: paragraphs = [], isLoading: paragraphsLoading } = useParagraphs(
    selectedChapterId || 0,
    isSchool,
    !!selectedChapterId && selectedChapterId > 0
  );

  // Reset chapter and paragraph when textbook changes (only on create)
  useEffect(() => {
    if (!test && selectedTextbookId > 0) {
      const currentChapterId = form.getValues('chapter_id');
      // Only reset if current chapter doesn't belong to this textbook
      if (currentChapterId) {
        const chapterBelongsToTextbook = chapters.some(c => c.id === currentChapterId);
        if (!chapterBelongsToTextbook && chapters.length > 0) {
          form.setValue('chapter_id', undefined);
          form.setValue('paragraph_id', undefined);
        }
      }
    }
  }, [selectedTextbookId, chapters, form, test]);

  // Reset paragraph when chapter changes (only on create)
  useEffect(() => {
    if (!test && selectedChapterId) {
      const currentParagraphId = form.getValues('paragraph_id');
      // Only reset if current paragraph doesn't belong to this chapter
      if (currentParagraphId) {
        const paragraphBelongsToChapter = paragraphs.some(p => p.id === currentParagraphId);
        if (!paragraphBelongsToChapter && paragraphs.length > 0) {
          form.setValue('paragraph_id', undefined);
        }
      }
    }
  }, [selectedChapterId, paragraphs, form, test]);

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <FormField
          control={form.control}
          name="title"
          render={({ field }) => (
            <FormItem>
              <FormLabel>{t('testTitle')} *</FormLabel>
              <FormControl>
                <Input placeholder="Тест по главе 1: Числа и выражения" {...field} />
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
              <FormLabel>{t('description')}</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="Описание теста..."
                  className="min-h-[80px]"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Cascading Textbook/Chapter/Paragraph Selects */}
        <div className="space-y-4 rounded-lg border p-4">
          <h3 className="font-medium">Привязка к контенту</h3>

          <div className="grid gap-4 md:grid-cols-3">
            {/* Textbook Select - Required */}
            <FormField
              control={form.control}
              name="textbook_id"
              render={({ field }) => (
                <FormItem className="min-w-0">
                  <FormLabel>Учебник *</FormLabel>
                  <Select
                    onValueChange={(value) => field.onChange(parseInt(value))}
                    value={field.value ? String(field.value) : undefined}
                    disabled={textbooksLoading}
                  >
                    <FormControl>
                      <SelectTrigger className="w-full h-auto min-h-9 whitespace-normal text-left [&>span]:line-clamp-2">
                        <SelectValue placeholder={textbooksLoading ? 'Загрузка...' : 'Выберите учебник'} />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {textbooks.map((textbook) => (
                        <SelectItem key={textbook.id} value={String(textbook.id)}>
                          {textbook.title} ({textbook.grade_level} класс)
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormDescription>Обязательное поле</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Chapter Select - Optional */}
            <FormField
              control={form.control}
              name="chapter_id"
              render={({ field }) => (
                <FormItem className="min-w-0">
                  <FormLabel>Глава</FormLabel>
                  <Select
                    onValueChange={(value) => field.onChange(value === 'none' ? undefined : parseInt(value))}
                    value={field.value ? String(field.value) : 'none'}
                    disabled={!selectedTextbookId || selectedTextbookId === 0 || chaptersLoading}
                  >
                    <FormControl>
                      <SelectTrigger className="w-full h-auto min-h-9 whitespace-normal text-left [&>span]:line-clamp-2">
                        <SelectValue placeholder={
                          !selectedTextbookId || selectedTextbookId === 0
                            ? 'Сначала выберите учебник'
                            : chaptersLoading
                              ? 'Загрузка...'
                              : 'Выберите главу'
                        } />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="none">Без привязки к главе</SelectItem>
                      {chapters.map((chapter) => (
                        <SelectItem key={chapter.id} value={String(chapter.id)}>
                          {chapter.number}. {chapter.title}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormDescription>Опционально</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Paragraph Select - Optional */}
            <FormField
              control={form.control}
              name="paragraph_id"
              render={({ field }) => (
                <FormItem className="min-w-0">
                  <FormLabel>Параграф</FormLabel>
                  <Select
                    onValueChange={(value) => field.onChange(value === 'none' ? undefined : parseInt(value))}
                    value={field.value ? String(field.value) : 'none'}
                    disabled={!selectedChapterId || paragraphsLoading}
                  >
                    <FormControl>
                      <SelectTrigger className="w-full h-auto min-h-9 whitespace-normal text-left [&>span]:line-clamp-2">
                        <SelectValue placeholder={
                          !selectedChapterId
                            ? 'Сначала выберите главу'
                            : paragraphsLoading
                              ? 'Загрузка...'
                              : 'Выберите параграф'
                        } />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="none">Без привязки к параграфу</SelectItem>
                      {paragraphs.map((paragraph) => (
                        <SelectItem key={paragraph.id} value={String(paragraph.id)}>
                          {paragraph.number}. {paragraph.title}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormDescription>Опционально</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <FormField
            control={form.control}
            name="test_purpose"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('testPurpose')} *</FormLabel>
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Выберите назначение" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {TEST_PURPOSES.map((purpose) => (
                      <SelectItem key={purpose.value} value={purpose.value}>
                        {purpose.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormDescription>
                  Тип проверки знаний
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="difficulty"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('difficulty')} *</FormLabel>
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Выберите сложность" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {DIFFICULTIES.map((diff) => (
                      <SelectItem key={diff.value} value={diff.value}>
                        {diff.label}
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
            name="time_limit"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('timeLimit')}</FormLabel>
                <FormControl>
                  <Input
                    type="number"
                    min={1}
                    max={180}
                    placeholder="30"
                    {...field}
                    onChange={(e) => field.onChange(e.target.value ? parseInt(e.target.value) : undefined)}
                    value={field.value ?? ''}
                  />
                </FormControl>
                <FormDescription>
                  Время в минутах (1-180)
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="passing_score"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('passingScore')} *</FormLabel>
                <FormControl>
                  <Input
                    type="number"
                    min={0}
                    max={100}
                    {...field}
                    onChange={(e) => field.onChange(parseInt(e.target.value) || 0)}
                  />
                </FormControl>
                <FormDescription>
                  Минимум % для прохождения (0-100)
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <FormField
          control={form.control}
          name="is_active"
          render={({ field }) => (
            <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
              <div className="space-y-0.5">
                <FormLabel className="text-base">Активен</FormLabel>
                <FormDescription>
                  Неактивные тесты не отображаются для учеников
                </FormDescription>
              </div>
              <FormControl>
                <Switch
                  checked={field.value}
                  onCheckedChange={field.onChange}
                />
              </FormControl>
            </FormItem>
          )}
        />

        <div className="flex justify-end gap-4">
          <Button type="submit" disabled={isLoading}>
            {isLoading ? tCommon('loading') : tCommon('save')}
          </Button>
        </div>
      </form>
    </Form>
  );
}
