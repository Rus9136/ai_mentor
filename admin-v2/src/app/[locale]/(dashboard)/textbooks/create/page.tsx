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
import { TextbookForm } from '@/components/forms';
import { useCreateTextbook } from '@/lib/hooks/use-textbooks';
import type { TextbookCreateInput } from '@/lib/validations/textbook';

export default function TextbookCreatePage() {
  const t = useTranslations('textbooks');
  const router = useRouter();
  const createTextbook = useCreateTextbook(false);

  const handleSubmit = (data: TextbookCreateInput) => {
    createTextbook.mutate(data, {
      onSuccess: () => {
        router.push('/ru/textbooks');
      },
    });
  };

  return (
    <RoleGuard allowedRoles={['super_admin']}>
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{t('create')}</h1>
            <p className="text-muted-foreground">
              Создание нового глобального учебника
            </p>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Информация об учебнике</CardTitle>
            <CardDescription>
              Поля отмеченные * обязательны для заполнения
            </CardDescription>
          </CardHeader>
          <CardContent>
            <TextbookForm
              onSubmit={handleSubmit}
              isLoading={createTextbook.isPending}
            />
          </CardContent>
        </Card>
      </div>
    </RoleGuard>
  );
}
