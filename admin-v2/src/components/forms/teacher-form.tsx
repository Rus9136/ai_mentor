'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useTranslations } from 'next-intl';
import { X } from 'lucide-react';

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
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
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

  // Resolve initial subject_ids from teacher data (prefer subject_ids, fallback to subject_id)
  const initialSubjectIds = teacher
    ? teacher.subject_ids && teacher.subject_ids.length > 0
      ? teacher.subject_ids
      : teacher.subject_id
        ? [teacher.subject_id]
        : []
    : [];

  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: teacher
      ? {
          first_name: teacher.user?.first_name || '',
          last_name: teacher.user?.last_name || '',
          middle_name: teacher.user?.middle_name || '',
          phone: teacher.user?.phone || '',
          teacher_code: teacher.teacher_code || '',
          subject_ids: initialSubjectIds,
          bio: teacher.bio || '',
        }
      : teacherCreateDefaults,
  });

  const handleFormSubmit = (data: TeacherCreateInput | TeacherUpdateInput) => {
    // Clean empty strings → undefined so backend doesn't receive invalid empty email/phone
    const cleaned = { ...data };
    if ('email' in cleaned && !cleaned.email) delete cleaned.email;
    if ('phone' in cleaned && !cleaned.phone) delete cleaned.phone;
    if ('middle_name' in cleaned && !cleaned.middle_name) delete cleaned.middle_name;
    if ('teacher_code' in cleaned && !cleaned.teacher_code) delete cleaned.teacher_code;
    if ('bio' in cleaned && !cleaned.bio) delete cleaned.bio;
    onSubmit(cleaned as never);
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleFormSubmit)} className="space-y-6">
        {!isEdit && (
          <>
            <div className="grid gap-6 md:grid-cols-3">
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input type="email" placeholder="teacher@school.com" {...field} />
                    </FormControl>
                    <FormDescription>Укажите email или телефон (или оба)</FormDescription>
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
                      <Input type="tel" placeholder="+77771234567" {...field} />
                    </FormControl>
                    <FormDescription>Формат: +7XXXXXXXXXX</FormDescription>
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
                      <Input type="password" placeholder="Минимум 8 символов" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          </>
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
            name="subject_ids"
            render={({ field }) => {
              const selectedIds: number[] = field.value || [];
              const selectedSubjects = subjects?.filter((s) => selectedIds.includes(s.id)) || [];

              const toggleSubject = (subjectId: number) => {
                const current = field.value || [];
                if (current.includes(subjectId)) {
                  field.onChange(current.filter((id: number) => id !== subjectId));
                } else {
                  field.onChange([...current, subjectId]);
                }
              };

              return (
                <FormItem className="md:col-span-2">
                  <FormLabel>{t('subject')}</FormLabel>
                  <Popover>
                    <PopoverTrigger asChild>
                      <FormControl>
                        <Button
                          variant="outline"
                          role="combobox"
                          type="button"
                          className="w-full justify-start font-normal min-h-[40px] h-auto"
                          disabled={subjectsLoading}
                        >
                          {selectedSubjects.length > 0 ? (
                            <div className="flex flex-wrap gap-1">
                              {selectedSubjects.map((s) => (
                                <Badge
                                  key={s.id}
                                  variant="secondary"
                                  className="mr-1"
                                >
                                  {s.name_ru}
                                  <button
                                    type="button"
                                    className="ml-1 ring-offset-background rounded-full outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      toggleSubject(s.id);
                                    }}
                                  >
                                    <X className="h-3 w-3" />
                                  </button>
                                </Badge>
                              ))}
                            </div>
                          ) : (
                            <span className="text-muted-foreground">
                              {subjectsLoading ? 'Загрузка...' : 'Выберите предметы'}
                            </span>
                          )}
                        </Button>
                      </FormControl>
                    </PopoverTrigger>
                    <PopoverContent className="w-[400px] p-0" align="start">
                      <div className="max-h-[300px] overflow-y-auto p-2 space-y-1">
                        {subjects?.map((subject) => (
                          <label
                            key={subject.id}
                            className="flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-accent cursor-pointer"
                          >
                            <Checkbox
                              checked={selectedIds.includes(subject.id)}
                              onCheckedChange={() => toggleSubject(subject.id)}
                            />
                            <span className="text-sm">{subject.name_ru}</span>
                          </label>
                        ))}
                      </div>
                    </PopoverContent>
                  </Popover>
                  <FormMessage />
                </FormItem>
              );
            }}
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

          {isEdit && (
            <FormField
              control={form.control}
              name="phone"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Телефон</FormLabel>
                  <FormControl>
                    <Input type="tel" placeholder="+77771234567" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          )}
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
