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
  studentCreateSchema,
  studentUpdateSchema,
  studentCreateDefaults,
  type StudentCreateInput,
  type StudentUpdateInput,
} from '@/lib/validations/student';
import type { Student } from '@/types';

type StudentFormProps =
  | {
      mode: 'create';
      student?: never;
      onSubmit: (data: StudentCreateInput) => void;
      isLoading?: boolean;
    }
  | {
      mode: 'edit';
      student: Student;
      onSubmit: (data: StudentUpdateInput) => void;
      isLoading?: boolean;
    };

const gradeOptions = Array.from({ length: 11 }, (_, i) => i + 1);

export function StudentForm(props: StudentFormProps) {
  const { onSubmit, isLoading, mode } = props;
  const student = mode === 'edit' ? props.student : undefined;

  const t = useTranslations('students');
  const tCommon = useTranslations('common');

  const isEdit = mode === 'edit';
  const schema = isEdit ? studentUpdateSchema : studentCreateSchema;

  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: student
      ? {
          first_name: student.user?.first_name || '',
          last_name: student.user?.last_name || '',
          middle_name: student.user?.middle_name || '',
          phone: student.user?.phone || '',
          student_code: student.student_code || '',
          grade_level: student.grade_level,
          birth_date: student.birth_date || '',
          enrollment_date: student.enrollment_date || '',
        }
      : studentCreateDefaults,
  });

  const handleFormSubmit = (data: StudentCreateInput | StudentUpdateInput) => {
    // Type assertion based on mode
    onSubmit(data as never);
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleFormSubmit)} className="space-y-6">
        {!isEdit && (
          <div className="grid gap-6 md:grid-cols-2">
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email *</FormLabel>
                  <FormControl>
                    <Input type="email" placeholder="student@school.com" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Пароль *</FormLabel>
                  <FormControl>
                    <Input type="password" placeholder="Минимум 6 символов" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
        )}

        <div className="grid gap-6 md:grid-cols-3">
          <FormField
            control={form.control}
            name="last_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('lastName')} *</FormLabel>
                <FormControl>
                  <Input placeholder="Иванов" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="first_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('firstName')} *</FormLabel>
                <FormControl>
                  <Input placeholder="Иван" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="middle_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('middleName')}</FormLabel>
                <FormControl>
                  <Input placeholder="Петрович" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <div className="grid gap-6 md:grid-cols-3">
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
                      <SelectValue placeholder="Выберите класс" />
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
            name="student_code"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('studentCode')}</FormLabel>
                <FormControl>
                  <Input placeholder="STU-001" {...field} />
                </FormControl>
                <FormDescription>Табельный номер</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="phone"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Телефон</FormLabel>
                <FormControl>
                  <Input placeholder="+7 (777) 123-45-67" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <FormField
            control={form.control}
            name="birth_date"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('birthDate')}</FormLabel>
                <FormControl>
                  <Input type="date" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="enrollment_date"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('enrollmentDate')}</FormLabel>
                <FormControl>
                  <Input type="date" {...field} />
                </FormControl>
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
