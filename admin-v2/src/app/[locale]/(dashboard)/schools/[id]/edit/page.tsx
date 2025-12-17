'use client';

import { useParams, useRouter } from 'next/navigation';
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
import { SchoolForm } from '@/components/forms';
import { useSchool, useUpdateSchool } from '@/lib/hooks/use-schools';
import type { SchoolCreateInput } from '@/lib/validations/school';

export default function SchoolEditPage() {
  const t = useTranslations('schools');
  const params = useParams();
  const router = useRouter();
  const schoolId = Number(params.id);

  const { data: school, isLoading } = useSchool(schoolId);
  const updateSchool = useUpdateSchool();

  const handleSubmit = (data: SchoolCreateInput) => {
    updateSchool.mutate(
      { id: schoolId, data },
      {
        onSuccess: () => {
          router.push(`/ru/schools/${schoolId}`);
        },
      }
    );
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10" />
          <Skeleton className="h-8 w-48" />
        </div>
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
          </CardHeader>
          <CardContent className="space-y-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!school) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <p className="text-muted-foreground">Школа не найдена</p>
        <Button variant="link" onClick={() => router.back()}>
          Вернуться назад
        </Button>
      </div>
    );
  }

  return (
    <RoleGuard allowedRoles={['super_admin']}>
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">
              {t('edit')}: {school.name}
            </h1>
            <p className="text-muted-foreground">
              Измените данные школы
            </p>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Информация о школе</CardTitle>
            <CardDescription>
              Поля отмеченные * обязательны для заполнения
            </CardDescription>
          </CardHeader>
          <CardContent>
            <SchoolForm
              school={school}
              onSubmit={handleSubmit}
              isLoading={updateSchool.isPending}
            />
          </CardContent>
        </Card>
      </div>
    </RoleGuard>
  );
}
