'use client';

import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { ArrowLeft } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { RoleGuard } from '@/components/auth';
import { TeacherForm } from '@/components/forms';
import { useCreateTeacher } from '@/lib/hooks';
import type { TeacherCreateInput } from '@/lib/validations/teacher';

export default function TeacherCreatePage() {
  const t = useTranslations('teachers');
  const router = useRouter();
  const createTeacher = useCreateTeacher();

  const handleSubmit = (data: TeacherCreateInput) => {
    createTeacher.mutate(data, {
      onSuccess: () => {
        router.push('/ru/teachers');
      },
    });
  };

  return (
    <RoleGuard allowedRoles={['admin']}>
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.back()}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{t('create')}</h1>
            <p className="text-muted-foreground">
              Заполните форму для добавления нового учителя
            </p>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Данные учителя</CardTitle>
            <CardDescription>
              Поля отмеченные * обязательны для заполнения
            </CardDescription>
          </CardHeader>
          <CardContent>
            <TeacherForm
              onSubmit={handleSubmit}
              isLoading={createTeacher.isPending}
              mode="create"
            />
          </CardContent>
        </Card>
      </div>
    </RoleGuard>
  );
}
