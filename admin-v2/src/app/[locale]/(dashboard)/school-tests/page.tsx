'use client';

import { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import { FileQuestion, Plus, Eye, Edit, Trash2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { DataTable } from '@/components/data-table';
import { DataTableColumnHeader, DataTableRowActions } from '@/components/data-table';
import { RoleGuard } from '@/components/auth';
import { useSchoolTests, useDeleteSchoolTest } from '@/lib/hooks';
import type { Test, DifficultyLevel, TestPurpose } from '@/types';
import { type ColumnDef } from '@tanstack/react-table';

const difficultyLabels: Record<DifficultyLevel, string> = {
  easy: 'Легкий',
  medium: 'Средний',
  hard: 'Сложный',
};

const difficultyColors: Record<DifficultyLevel, 'default' | 'secondary' | 'destructive'> = {
  easy: 'default',
  medium: 'secondary',
  hard: 'destructive',
};

const purposeLabels: Record<TestPurpose, string> = {
  diagnostic: 'Диагностический',
  formative: 'Формативный',
  summative: 'Суммативный',
  practice: 'Практический',
};

export default function SchoolTestsPage() {
  const router = useRouter();
  const locale = 'ru';

  const { data: tests = [], isLoading } = useSchoolTests();
  const deleteTest = useDeleteSchoolTest();

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [testToDelete, setTestToDelete] = useState<Test | null>(null);

  const handleView = (test: Test) => {
    router.push(`/${locale}/school-tests/${test.id}`);
  };

  const handleEdit = (test: Test) => {
    router.push(`/${locale}/school-tests/${test.id}/edit`);
  };

  const handleDelete = (test: Test) => {
    setTestToDelete(test);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (testToDelete) {
      deleteTest.mutate(testToDelete.id);
    }
    setDeleteDialogOpen(false);
    setTestToDelete(null);
  };

  const columns: ColumnDef<Test>[] = useMemo(
    () => [
      {
        accessorKey: 'id',
        header: ({ column }) => (
          <DataTableColumnHeader column={column} title="ID" />
        ),
        cell: ({ row }) => <div className="w-[40px]">{row.getValue('id')}</div>,
      },
      {
        accessorKey: 'title',
        header: ({ column }) => (
          <DataTableColumnHeader column={column} title="Название" />
        ),
        cell: ({ row }) => (
          <div className="max-w-[300px]">
            <div className="font-medium truncate">{row.getValue('title')}</div>
            {row.original.description && (
              <div className="text-sm text-muted-foreground truncate">
                {row.original.description}
              </div>
            )}
          </div>
        ),
      },
      {
        accessorKey: 'test_purpose',
        header: ({ column }) => (
          <DataTableColumnHeader column={column} title="Назначение" />
        ),
        cell: ({ row }) => (
          <Badge variant="outline">
            {purposeLabels[row.getValue('test_purpose') as TestPurpose]}
          </Badge>
        ),
      },
      {
        accessorKey: 'difficulty',
        header: ({ column }) => (
          <DataTableColumnHeader column={column} title="Сложность" />
        ),
        cell: ({ row }) => {
          const difficulty = row.getValue('difficulty') as DifficultyLevel;
          return (
            <Badge variant={difficultyColors[difficulty]}>
              {difficultyLabels[difficulty]}
            </Badge>
          );
        },
      },
      {
        accessorKey: 'passing_score',
        header: ({ column }) => (
          <DataTableColumnHeader column={column} title="Проходной балл" />
        ),
        cell: ({ row }) => `${row.getValue('passing_score')}%`,
      },
      {
        accessorKey: 'created_at',
        header: ({ column }) => (
          <DataTableColumnHeader column={column} title="Создан" />
        ),
        cell: ({ row }) => {
          const date = row.getValue('created_at') as string;
          return (
            <div className="text-muted-foreground">
              {format(new Date(date), 'dd.MM.yyyy', { locale: ru })}
            </div>
          );
        },
      },
      {
        id: 'actions',
        cell: ({ row }) => {
          const test = row.original;
          return (
            <DataTableRowActions
              onView={() => handleView(test)}
              onEdit={() => handleEdit(test)}
              onDelete={() => handleDelete(test)}
            />
          );
        },
      },
    ],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  if (isLoading) {
    return (
      <RoleGuard allowedRoles={['admin']}>
        <div className="space-y-6">
          <Skeleton className="h-10 w-64" />
          <Skeleton className="h-[400px] w-full" />
        </div>
      </RoleGuard>
    );
  }

  return (
    <RoleGuard allowedRoles={['admin']}>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Тесты школы</h1>
            <p className="text-muted-foreground">
              Управление тестами вашей школы
            </p>
          </div>
          <Button onClick={() => router.push(`/${locale}/school-tests/create`)}>
            <Plus className="mr-2 h-4 w-4" />
            Создать тест
          </Button>
        </div>

        {tests.length > 0 ? (
          <DataTable
            columns={columns}
            data={tests}
            searchKey="title"
            searchPlaceholder="Поиск по названию..."
          />
        ) : (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <FileQuestion className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground mb-4">У вас пока нет тестов</p>
              <Button onClick={() => router.push(`/${locale}/school-tests/create`)}>
                <Plus className="mr-2 h-4 w-4" />
                Создать первый тест
              </Button>
            </CardContent>
          </Card>
        )}

        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Удалить тест?</AlertDialogTitle>
              <AlertDialogDescription>
                Вы уверены, что хотите удалить тест &quot;{testToDelete?.title}&quot;?
                Все вопросы будут удалены.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Отмена</AlertDialogCancel>
              <AlertDialogAction
                onClick={confirmDelete}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              >
                Удалить
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </RoleGuard>
  );
}
