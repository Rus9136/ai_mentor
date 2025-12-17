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
import { SchoolForm } from '@/components/forms';
import { useCreateSchool } from '@/lib/hooks/use-schools';
import type { SchoolCreateInput } from '@/lib/validations/school';

export default function SchoolCreatePage() {
  const t = useTranslations('schools');
  const router = useRouter();
  const createSchool = useCreateSchool();

  const handleSubmit = (data: SchoolCreateInput) => {
    createSchool.mutate(data, {
      onSuccess: () => {
        router.push('/ru/schools');
      },
    });
  };

  return (
    <RoleGuard allowedRoles={['super_admin']}>
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
              Заполните форму для создания новой школы
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
              onSubmit={handleSubmit}
              isLoading={createSchool.isPending}
            />
          </CardContent>
        </Card>
      </div>
    </RoleGuard>
  );
}
