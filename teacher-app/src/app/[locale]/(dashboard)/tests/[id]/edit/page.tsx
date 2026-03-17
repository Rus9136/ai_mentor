'use client';

import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TestForm } from '@/components/tests/test-form';
import { useTeacherTest, useUpdateTeacherTest } from '@/lib/hooks/use-teacher-tests';
import type { TestCreate } from '@/types/test';

export default function EditTeacherTestPage() {
  const params = useParams();
  const router = useRouter();
  const locale = 'ru';
  const testId = Number(params.id);

  const { data: test, isLoading: testLoading } = useTeacherTest(testId);
  const updateTest = useUpdateTeacherTest();

  const handleSubmit = (data: TestCreate) => {
    updateTest.mutate(
      { id: testId, data },
      {
        onSuccess: () => {
          router.push(`/${locale}/tests/${testId}`);
        },
      }
    );
  };

  if (testLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-muted animate-pulse rounded" />
        <div className="h-[400px] w-full bg-muted animate-pulse rounded" />
      </div>
    );
  }

  if (!test) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Тест не найден</p>
        <Button variant="link" onClick={() => router.push(`/${locale}/tests`)}>
          Вернуться к списку
        </Button>
      </div>
    );
  }

  if (test.school_id === null) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Глобальные тесты нельзя редактировать</p>
        <Button variant="link" onClick={() => router.push(`/${locale}/tests/${testId}`)}>
          Назад к тесту
        </Button>
      </div>
    );
  }

  return (
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
          <h1 className="text-3xl font-bold tracking-tight">Редактировать тест</h1>
          <p className="text-muted-foreground">{test.title}</p>
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
  );
}
