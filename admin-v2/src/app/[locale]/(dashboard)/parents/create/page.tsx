'use client';

import { useRouter } from 'next/navigation';
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
import { ParentForm } from '@/components/forms';
import { useCreateParent, useStudents } from '@/lib/hooks';
import type { ParentCreateInput } from '@/lib/validations/parent';

export default function ParentCreatePage() {
  const router = useRouter();
  const createParent = useCreateParent();
  const { data: students = [] } = useStudents();

  const handleSubmit = (data: ParentCreateInput) => {
    createParent.mutate(data, {
      onSuccess: () => {
        router.push('/ru/parents');
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
            <h1 className="text-3xl font-bold tracking-tight">Добавить родителя</h1>
            <p className="text-muted-foreground">
              Заполните форму для регистрации родителя
            </p>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Данные родителя</CardTitle>
            <CardDescription>
              Поля отмеченные * обязательны. Можно сразу привязать детей.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ParentForm
              students={students}
              onSubmit={handleSubmit}
              isLoading={createParent.isPending}
            />
          </CardContent>
        </Card>
      </div>
    </RoleGuard>
  );
}
