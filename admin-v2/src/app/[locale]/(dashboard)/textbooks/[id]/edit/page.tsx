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
import { TextbookForm } from '@/components/forms';
import { useTextbook, useUpdateTextbook } from '@/lib/hooks/use-textbooks';
import type { TextbookCreateInput } from '@/lib/validations/textbook';

export default function TextbookEditPage() {
  const t = useTranslations('textbooks');
  const params = useParams();
  const router = useRouter();
  const textbookId = Number(params.id);

  const { data: textbook, isLoading } = useTextbook(textbookId, false);
  const updateTextbook = useUpdateTextbook(false);

  const handleSubmit = (data: TextbookCreateInput) => {
    updateTextbook.mutate(
      { id: textbookId, data },
      {
        onSuccess: () => {
          router.push(`/ru/textbooks/${textbookId}`);
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
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!textbook) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <p className="text-muted-foreground">Учебник не найден</p>
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
              {t('edit')}: {textbook.title}
            </h1>
            <p className="text-muted-foreground">
              Редактирование учебника
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
              textbook={textbook}
              onSubmit={handleSubmit}
              isLoading={updateTextbook.isPending}
            />
          </CardContent>
        </Card>
      </div>
    </RoleGuard>
  );
}
