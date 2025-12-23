'use client';

import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { ArrowLeft } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { RoleGuard } from '@/components/auth';
import { TestForm } from '@/components/forms/test-form';
import { useCreateTest } from '@/lib/hooks/use-tests';
import type { TestCreateInput } from '@/lib/validations/test';

export default function CreateTestPage() {
  const t = useTranslations('tests');
  const router = useRouter();
  const locale = 'ru';

  const createTest = useCreateTest(false); // global test

  const handleSubmit = (data: TestCreateInput) => {
    createTest.mutate(data, {
      onSuccess: (newTest) => {
        router.push(`/${locale}/tests/${newTest.id}`);
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
            onClick={() => router.push(`/${locale}/tests`)}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{t('createTitle')}</h1>
            <p className="text-muted-foreground">
              Создание нового глобального теста
            </p>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Информация о тесте</CardTitle>
          </CardHeader>
          <CardContent>
            <TestForm onSubmit={handleSubmit} isLoading={createTest.isPending} isSchool={false} />
          </CardContent>
        </Card>
      </div>
    </RoleGuard>
  );
}
