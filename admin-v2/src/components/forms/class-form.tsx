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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  classCreateSchema,
  classCreateDefaults,
  type ClassCreateInput,
} from '@/lib/validations/class';
import type { SchoolClass } from '@/types';

interface ClassFormProps {
  schoolClass?: SchoolClass;
  onSubmit: (data: ClassCreateInput) => void;
  isLoading?: boolean;
}

const gradeOptions = Array.from({ length: 11 }, (_, i) => i + 1);
const currentYear = new Date().getFullYear();
const yearOptions = [
  `${currentYear - 1}-${currentYear}`,
  `${currentYear}-${currentYear + 1}`,
  `${currentYear + 1}-${currentYear + 2}`,
];

export function ClassForm({ schoolClass, onSubmit, isLoading }: ClassFormProps) {
  const t = useTranslations('classes');
  const tCommon = useTranslations('common');

  const form = useForm<ClassCreateInput>({
    resolver: zodResolver(classCreateSchema),
    defaultValues: schoolClass
      ? {
          name: schoolClass.name,
          code: schoolClass.code,
          grade_level: schoolClass.grade_level,
          academic_year: schoolClass.academic_year,
        }
      : classCreateDefaults,
  });

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <div className="grid gap-6 md:grid-cols-2">
          <FormField
            control={form.control}
            name="name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('name')} *</FormLabel>
                <FormControl>
                  <Input placeholder="7А" {...field} />
                </FormControl>
                <FormDescription>Например: 7А, 8Б, 9В</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="code"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('code')} *</FormLabel>
                <FormControl>
                  <Input placeholder="7a-2024" {...field} />
                </FormControl>
                <FormDescription>Уникальный код класса</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <FormField
            control={form.control}
            name="grade_level"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('gradeLevel')} *</FormLabel>
                <Select
                  onValueChange={(value) => field.onChange(parseInt(value))}
                  defaultValue={field.value?.toString()}
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Выберите параллель" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {gradeOptions.map((grade) => (
                      <SelectItem key={grade} value={grade.toString()}>
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
            name="academic_year"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('academicYear')} *</FormLabel>
                <Select
                  onValueChange={field.onChange}
                  defaultValue={field.value}
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Выберите учебный год" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {yearOptions.map((year) => (
                      <SelectItem key={year} value={year}>
                        {year}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <div className="flex justify-end gap-4">
          <Button type="submit" disabled={isLoading}>
            {isLoading ? tCommon('loading') : tCommon('save')}
          </Button>
        </div>
      </form>
    </Form>
  );
}
