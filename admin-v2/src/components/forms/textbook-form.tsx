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
  textbookCreateSchema,
  textbookCreateDefaults,
  type TextbookCreateInput,
} from '@/lib/validations/textbook';
import { useSubjects } from '@/lib/hooks/use-goso';
import type { Textbook } from '@/types';

interface TextbookFormProps {
  textbook?: Textbook;
  onSubmit: (data: TextbookCreateInput) => void;
  isLoading?: boolean;
}

const GRADES = [7, 8, 9, 10, 11];

export function TextbookForm({ textbook, onSubmit, isLoading }: TextbookFormProps) {
  const t = useTranslations('textbooks');
  const tCommon = useTranslations('common');
  const { data: subjects, isLoading: subjectsLoading } = useSubjects();

  const form = useForm<TextbookCreateInput>({
    resolver: zodResolver(textbookCreateSchema),
    defaultValues: textbook
      ? {
          title: textbook.title,
          subject_id: textbook.subject_id || 0,
          grade_level: textbook.grade_level,
          author: textbook.author || '',
          publisher: textbook.publisher || '',
          year: textbook.year || new Date().getFullYear(),
          isbn: textbook.isbn || '',
          description: textbook.description || '',
          is_active: textbook.is_active,
        }
      : textbookCreateDefaults,
  });

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <div className="grid gap-6 md:grid-cols-2">
          <FormField
            control={form.control}
            name="title"
            render={({ field }) => (
              <FormItem className="md:col-span-2">
                <FormLabel>{t('textbookTitle')} *</FormLabel>
                <FormControl>
                  <Input placeholder="Алгебра 7 класс" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="subject_id"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('subject')} *</FormLabel>
                <Select
                  onValueChange={(v) => field.onChange(parseInt(v))}
                  defaultValue={field.value ? String(field.value) : undefined}
                  disabled={subjectsLoading}
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder={subjectsLoading ? 'Загрузка...' : 'Выберите предмет'} />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {subjects?.map((subject) => (
                      <SelectItem key={subject.id} value={String(subject.id)}>
                        {subject.name_ru}
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
            name="grade_level"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('gradeLevel')} *</FormLabel>
                <Select
                  onValueChange={(v) => field.onChange(parseInt(v))}
                  defaultValue={String(field.value)}
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Выберите класс" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {GRADES.map((grade) => (
                      <SelectItem key={grade} value={String(grade)}>
                        {grade} класс
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
            name="author"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('author')}</FormLabel>
                <FormControl>
                  <Input placeholder="Иванов И.И." {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="publisher"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('publisher')}</FormLabel>
                <FormControl>
                  <Input placeholder="Издательство" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="year"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('year')}</FormLabel>
                <FormControl>
                  <Input
                    type="number"
                    min={1900}
                    max={2100}
                    {...field}
                    onChange={(e) => field.onChange(e.target.value ? parseInt(e.target.value) : undefined)}
                    value={field.value ?? ''}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="isbn"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('isbn')}</FormLabel>
                <FormControl>
                  <Input placeholder="978-5-00-000000-0" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <FormLabel>{t('description')}</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="Описание учебника..."
                  className="min-h-[100px]"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="is_active"
          render={({ field }) => (
            <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
              <div className="space-y-0.5">
                <FormLabel className="text-base">Активен</FormLabel>
                <FormDescription>
                  Неактивные учебники не отображаются для учеников
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
