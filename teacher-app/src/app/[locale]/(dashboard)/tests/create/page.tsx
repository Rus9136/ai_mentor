'use client';

import { useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TestForm } from '@/components/tests/test-form';
import { useCreateTeacherTest } from '@/lib/hooks/use-teacher-tests';
import type { TestCreate } from '@/types/test';

export default function CreateTeacherTestPage() {
  const router = useRouter();
  const locale = 'ru';
  const createTest = useCreateTeacherTest();

  const handleSubmit = (data: TestCreate) => {
    createTest.mutate(data, {
      onSuccess: (newTest) => {
        router.push(`/${locale}/tests/${newTest.id}`);
      },
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.push(`/${locale}/tests`)}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Создать тест</h1>
          <p className="text-muted-foreground">Создание нового теста</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Информация о тесте</CardTitle>
        </CardHeader>
        <CardContent>
          <TestForm onSubmit={handleSubmit} isLoading={createTest.isPending} />
        </CardContent>
      </Card>
    </div>
  );
}
