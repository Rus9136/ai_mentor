'use client';

import { use } from 'react';
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
import { Skeleton } from '@/components/ui/skeleton';
import { RoleGuard } from '@/components/auth';
import { StudentForm } from '@/components/forms';
import { useStudent, useUpdateStudent } from '@/lib/hooks';
import type { StudentUpdateInput } from '@/lib/validations/student';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function StudentEditPage({ params }: PageProps) {
  const { id } = use(params);
  const studentId = parseInt(id);
  const t = useTranslations('students');
  const router = useRouter();

  const { data: student, isLoading } = useStudent(studentId);
  const updateStudent = useUpdateStudent();

  const handleSubmit = (data: StudentUpdateInput) => {
    updateStudent.mutate(
      { id: studentId, data },
      {
        onSuccess: () => {
          router.push(`/ru/students/${studentId}`);
        },
      }
    );
  };

  if (isLoading) {
    return (
      <RoleGuard allowedRoles={['admin']}>
        <div className="space-y-6">
          <div className="flex items-center gap-4">
            <Skeleton className="h-10 w-10" />
            <Skeleton className="h-10 w-64" />
          </div>
          <Card>
            <CardHeader>
              <Skeleton className="h-6 w-48" />
            </CardHeader>
            <CardContent className="space-y-4">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </CardContent>
          </Card>
        </div>
      </RoleGuard>
    );
  }

  if (!student) {
    return (
      <RoleGuard allowedRoles={['admin']}>
        <div className="flex flex-col items-center justify-center py-12">
          <p className="text-muted-foreground">Ученик не найден</p>
          <Button variant="link" onClick={() => router.back()}>
            Вернуться назад
          </Button>
        </div>
      </RoleGuard>
    );
  }

  return (
    <RoleGuard allowedRoles={['admin']}>
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{t('edit')}</h1>
            <p className="text-muted-foreground">
              {student.user?.last_name} {student.user?.first_name}
            </p>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Редактирование данных</CardTitle>
            <CardDescription>
              Измените необходимые поля
            </CardDescription>
          </CardHeader>
          <CardContent>
            <StudentForm
              student={student}
              onSubmit={handleSubmit}
              isLoading={updateStudent.isPending}
              mode="edit"
            />
          </CardContent>
        </Card>
      </div>
    </RoleGuard>
  );
}
