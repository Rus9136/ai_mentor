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
import { StudentForm } from '@/components/forms';
import { useCreateStudent } from '@/lib/hooks';
import type { StudentCreateInput } from '@/lib/validations/student';

export default function StudentCreatePage() {
  const t = useTranslations('students');
  const router = useRouter();
  const createStudent = useCreateStudent();

  const handleSubmit = (data: StudentCreateInput) => {
    createStudent.mutate(data, {
      onSuccess: () => {
        router.push('/ru/students');
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
              Заполните форму для добавления нового ученика
            </p>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Данные ученика</CardTitle>
            <CardDescription>
              Поля отмеченные * обязательны для заполнения
            </CardDescription>
          </CardHeader>
          <CardContent>
            <StudentForm
              onSubmit={handleSubmit}
              isLoading={createStudent.isPending}
              mode="create"
            />
          </CardContent>
        </Card>
      </div>
    </RoleGuard>
  );
}
