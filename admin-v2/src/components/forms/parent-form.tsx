'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useTranslations } from 'next-intl';

import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import {
  parentCreateSchema,
  parentCreateDefaults,
  type ParentCreateInput,
} from '@/lib/validations/parent';
import type { Student } from '@/types';

interface ParentFormProps {
  students?: Student[];
  onSubmit: (data: ParentCreateInput) => void;
  isLoading?: boolean;
}

export function ParentForm({ students = [], onSubmit, isLoading }: ParentFormProps) {
  const tCommon = useTranslations('common');

  const form = useForm<ParentCreateInput>({
    resolver: zodResolver(parentCreateSchema),
    defaultValues: parentCreateDefaults,
  });

  const selectedChildren = form.watch('child_ids') || [];

  const toggleChild = (studentId: number) => {
    const current = form.getValues('child_ids') || [];
    if (current.includes(studentId)) {
      form.setValue('child_ids', current.filter((id) => id !== studentId));
    } else {
      form.setValue('child_ids', [...current, studentId]);
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <div className="grid gap-6 md:grid-cols-2">
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email *</FormLabel>
                <FormControl>
                  <Input type="email" placeholder="parent@email.com" {...field} />
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

        <div className="grid gap-6 md:grid-cols-3">
          <FormField
            control={form.control}
            name="last_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Фамилия *</FormLabel>
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
                <FormLabel>Имя *</FormLabel>
                <FormControl>
                  <Input placeholder="Петр" {...field} />
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
                <FormLabel>Отчество</FormLabel>
                <FormControl>
                  <Input placeholder="Иванович" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

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

        {students.length > 0 && (
          <div className="space-y-3">
            <FormLabel>Дети (ученики школы)</FormLabel>
            <div className="grid gap-2 md:grid-cols-2">
              {students.map((student) => (
                <div
                  key={student.id}
                  className="flex items-center space-x-2 rounded-lg border p-3"
                >
                  <Checkbox
                    id={`student-${student.id}`}
                    checked={selectedChildren.includes(student.id)}
                    onCheckedChange={() => toggleChild(student.id)}
                  />
                  <label
                    htmlFor={`student-${student.id}`}
                    className="flex-1 cursor-pointer text-sm"
                  >
                    <span className="font-medium">
                      {student.user?.last_name} {student.user?.first_name}
                    </span>
                    <span className="ml-2 text-muted-foreground">
                      {student.grade_level} класс
                    </span>
                  </label>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex justify-end gap-4">
          <Button type="submit" disabled={isLoading}>
            {isLoading ? tCommon('loading') : tCommon('save')}
          </Button>
        </div>
      </form>
    </Form>
  );
}
