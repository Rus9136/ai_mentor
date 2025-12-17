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
import { ClassForm } from '@/components/forms';
import { useClass, useUpdateClass } from '@/lib/hooks';
import type { ClassCreateInput } from '@/lib/validations/class';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function ClassEditPage({ params }: PageProps) {
  const { id } = use(params);
  const classId = parseInt(id);
  const t = useTranslations('classes');
  const router = useRouter();

  const { data: schoolClass, isLoading } = useClass(classId);
  const updateClass = useUpdateClass();

  const handleSubmit = (data: ClassCreateInput) => {
    updateClass.mutate(
      { id: classId, data },
      {
        onSuccess: () => {
          router.push(`/ru/classes/${classId}`);
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
            </CardContent>
          </Card>
        </div>
      </RoleGuard>
    );
  }

  if (!schoolClass) {
    return (
      <RoleGuard allowedRoles={['admin']}>
        <div className="flex flex-col items-center justify-center py-12">
          <p className="text-muted-foreground">Класс не найден</p>
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
            <p className="text-muted-foreground">{schoolClass.name}</p>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Редактирование класса</CardTitle>
            <CardDescription>
              Измените необходимые поля
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ClassForm
              schoolClass={schoolClass}
              onSubmit={handleSubmit}
              isLoading={updateClass.isPending}
            />
          </CardContent>
        </Card>
      </div>
    </RoleGuard>
  );
}
