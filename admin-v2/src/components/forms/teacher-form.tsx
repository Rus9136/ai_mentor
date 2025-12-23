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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  teacherCreateSchema,
  teacherUpdateSchema,
  teacherCreateDefaults,
  type TeacherCreateInput,
  type TeacherUpdateInput,
} from '@/lib/validations/teacher';
import { useSubjects } from '@/lib/hooks/use-goso';
import type { Teacher } from '@/types';

type TeacherFormProps =
  | {
      mode: 'create';
      teacher?: never;
      onSubmit: (data: TeacherCreateInput) => void;
      isLoading?: boolean;
    }
  | {
      mode: 'edit';
      teacher: Teacher;
      onSubmit: (data: TeacherUpdateInput) => void;
      isLoading?: boolean;
    };

export function TeacherForm(props: TeacherFormProps) {
  const { onSubmit, isLoading, mode } = props;
  const teacher = mode === 'edit' ? props.teacher : undefined;

  const t = useTranslations('teachers');
  const tCommon = useTranslations('common');
  const { data: subjects, isLoading: subjectsLoading } = useSubjects();

  const isEdit = mode === 'edit';
  const schema = isEdit ? teacherUpdateSchema : teacherCreateSchema;

  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: teacher
      ? {
          first_name: teacher.user?.first_name || '',
          last_name: teacher.user?.last_name || '',
          middle_name: teacher.user?.middle_name || '',
          phone: teacher.user?.phone || '',
          teacher_code: teacher.teacher_code || '',
          subject_id: teacher.subject_id || null,
          bio: teacher.bio || '',
        }
      : teacherCreateDefaults,
  });

  const handleFormSubmit = (data: TeacherCreateInput | TeacherUpdateInput) => {
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
                    <Input type="email" placeholder="teacher@school.com" {...field} />
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
                  <Input placeholder="Петрова" {...field} />
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
                  <Input placeholder="Анна" {...field} />
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
                  <Input placeholder="Сергеевна" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          <FormField
            control={form.control}
            name="subject_id"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('subject')}</FormLabel>
                <Select
                  onValueChange={(v) => field.onChange(v ? parseInt(v) : null)}
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
            name="teacher_code"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('teacherCode')}</FormLabel>
                <FormControl>
                  <Input placeholder="TCH-001" {...field} />
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

        <FormField
          control={form.control}
          name="bio"
          render={({ field }) => (
            <FormItem>
              <FormLabel>{t('bio')}</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="Краткая информация об учителе..."
                  className="min-h-[100px]"
                  {...field}
                />
              </FormControl>
              <FormMessage />
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
