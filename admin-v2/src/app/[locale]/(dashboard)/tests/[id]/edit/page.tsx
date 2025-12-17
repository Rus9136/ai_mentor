'use client';

import { useParams, useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { ArrowLeft } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { RoleGuard } from '@/components/auth';
import { TestForm } from '@/components/forms/test-form';
import { useTest, useUpdateTest } from '@/lib/hooks/use-tests';
import type { TestCreateInput } from '@/lib/validations/test';

export default function EditTestPage() {
  const params = useParams();
  const router = useRouter();
  const t = useTranslations('tests');
  const locale = 'ru';

  const testId = Number(params.id);
  const { data: test, isLoading } = useTest(testId, false); // global test
  const updateTest = useUpdateTest(false);

  const handleSubmit = (data: TestCreateInput) => {
    updateTest.mutate(
      { id: testId, data },
      {
        onSuccess: () => {
          router.push(`/${locale}/tests/${testId}`);
        },
      }
    );
  };

  if (isLoading) {
    return (
      <RoleGuard allowedRoles={['super_admin']}>
        <div className="space-y-6">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-[400px] w-full" />
        </div>
      </RoleGuard>
    );
  }

  if (!test) {
    return (
      <RoleGuard allowedRoles={['super_admin']}>
        <div className="text-center py-12">
          <p className="text-muted-foreground">Тест не найден</p>
          <Button
            variant="link"
            onClick={() => router.push(`/${locale}/tests`)}
          >
            Вернуться к списку
          </Button>
        </div>
      </RoleGuard>
    );
  }

  return (
    <RoleGuard allowedRoles={['super_admin']}>
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push(`/${locale}/tests/${testId}`)}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{t('editTitle')}</h1>
            <p className="text-muted-foreground">
              Редактирование теста &quot;{test.title}&quot;
            </p>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Информация о тесте</CardTitle>
          </CardHeader>
          <CardContent>
            <TestForm
              test={test}
              onSubmit={handleSubmit}
              isLoading={updateTest.isPending}
            />
          </CardContent>
        </Card>
      </div>
    </RoleGuard>
  );
}
