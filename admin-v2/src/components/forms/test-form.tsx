'use client';

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
import type { Test } from '@/types';

interface TestFormProps {
  test?: Test;
  onSubmit: (data: TestCreateInput) => void;
  isLoading?: boolean;
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

export function TestForm({ test, onSubmit, isLoading }: TestFormProps) {
  const t = useTranslations('tests');
  const tCommon = useTranslations('common');

  const form = useForm<TestCreateInput>({
    resolver: zodResolver(testCreateSchema),
    defaultValues: test
      ? {
          title: test.title,
          description: test.description || '',
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
