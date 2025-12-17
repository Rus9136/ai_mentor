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
import { ClassForm } from '@/components/forms';
import { useCreateClass } from '@/lib/hooks';
import type { ClassCreateInput } from '@/lib/validations/class';

export default function ClassCreatePage() {
  const t = useTranslations('classes');
  const router = useRouter();
  const createClass = useCreateClass();

  const handleSubmit = (data: ClassCreateInput) => {
    createClass.mutate(data, {
      onSuccess: () => {
        router.push('/ru/classes');
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
              Создайте новый класс для школы
            </p>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Информация о классе</CardTitle>
            <CardDescription>
              Поля отмеченные * обязательны для заполнения
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ClassForm
              onSubmit={handleSubmit}
              isLoading={createClass.isPending}
            />
          </CardContent>
        </Card>
      </div>
    </RoleGuard>
  );
}
