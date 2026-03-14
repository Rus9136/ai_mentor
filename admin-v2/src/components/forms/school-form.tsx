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
import { Checkbox } from '@/components/ui/checkbox';
import { Separator } from '@/components/ui/separator';
import {
  schoolCreateSchema,
  schoolCreateDefaults,
  type SchoolCreateInput,
} from '@/lib/validations/school';
import type { School } from '@/types';

interface SchoolFormProps {
  school?: School;
  onSubmit: (data: SchoolCreateInput) => void;
  isLoading?: boolean;
}

export function SchoolForm({ school, onSubmit, isLoading }: SchoolFormProps) {
  const t = useTranslations('schools');
  const tCommon = useTranslations('common');
  const isEdit = !!school;

  const form = useForm<SchoolCreateInput>({
    resolver: zodResolver(schoolCreateSchema),
    defaultValues: school
      ? {
          name: school.name,
          code: school.code,
          email: school.email || '',
          phone: school.phone || '',
          address: school.address || '',
          description: school.description || '',
          create_admin: false,
        }
      : schoolCreateDefaults,
  });

  const createAdmin = form.watch('create_admin');

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
                  <Input placeholder="Школа №1" {...field} />
                </FormControl>
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
                  <Input placeholder="school-001" {...field} />
                </FormControl>
                <FormDescription>
                  Только lowercase буквы, цифры, дефисы и underscores
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('email')}</FormLabel>
                <FormControl>
                  <Input
                    type="email"
                    placeholder="school@example.com"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="phone"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('phone')}</FormLabel>
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
          name="address"
          render={({ field }) => (
            <FormItem>
              <FormLabel>{t('address')}</FormLabel>
              <FormControl>
                <Input placeholder="г. Алматы, ул. Абая, 1" {...field} />
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
                  placeholder="Описание школы..."
                  className="min-h-[100px]"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Admin section — only for create mode */}
        {!isEdit && (
          <>
            <Separator />

            <FormField
              control={form.control}
              name="create_admin"
              render={({ field }) => (
                <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                  <FormControl>
                    <Checkbox
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  </FormControl>
                  <div className="space-y-1 leading-none">
                    <FormLabel className="text-base font-semibold">
                      {t('adminSection')}
                    </FormLabel>
                    <FormDescription>
                      {t('adminSectionDescription')}
                    </FormDescription>
                  </div>
                </FormItem>
              )}
            />

            {createAdmin && (
              <div className="rounded-lg border p-4 space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <FormField
                    control={form.control}
                    name="admin.last_name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>{t('adminLastName')} *</FormLabel>
                        <FormControl>
                          <Input placeholder="Иванов" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="admin.first_name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>{t('adminFirstName')} *</FormLabel>
                        <FormControl>
                          <Input placeholder="Иван" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="admin.middle_name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>{t('adminMiddleName')}</FormLabel>
                        <FormControl>
                          <Input placeholder="Иванович" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <FormField
                    control={form.control}
                    name="admin.email"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>{t('adminEmail')} *</FormLabel>
                        <FormControl>
                          <Input
                            type="email"
                            placeholder="admin@school.com"
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="admin.password"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>{t('adminPassword')} *</FormLabel>
                        <FormControl>
                          <Input
                            type="password"
                            placeholder="Минимум 6 символов"
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              </div>
            )}
          </>
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
