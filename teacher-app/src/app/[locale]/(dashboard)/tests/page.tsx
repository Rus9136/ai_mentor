'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { Plus, FileQuestion, Eye, Edit, Trash2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useTeacherTests, useDeleteTeacherTest } from '@/lib/hooks/use-teacher-tests';
import type { Test, DifficultyLevel, TestPurpose } from '@/types/test';

const difficultyLabels: Record<DifficultyLevel, string> = {
  easy: 'Легкий',
  medium: 'Средний',
  hard: 'Сложный',
};

const difficultyVariants: Record<DifficultyLevel, 'default' | 'secondary' | 'destructive'> = {
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

export default function TeacherTestsPage() {
  const router = useRouter();
  const t = useTranslations('common');
  const locale = 'ru';

  const { data, isLoading } = useTeacherTests({ include_global: true });
  const deleteTest = useDeleteTeacherTest();

  const [search, setSearch] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [testToDelete, setTestToDelete] = useState<Test | null>(null);

  const tests = data?.items ?? [];

  const filtered = tests.filter(
    (test) =>
      test.title.toLowerCase().includes(search.toLowerCase()) ||
      (test.textbook_title && test.textbook_title.toLowerCase().includes(search.toLowerCase()))
  );

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

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-10 w-64 bg-muted animate-pulse rounded" />
        <div className="h-[400px] w-full bg-muted animate-pulse rounded" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Тесты</h1>
          <p className="text-muted-foreground">
            Тесты по вашему предмету
          </p>
        </div>
        <Button onClick={() => router.push(`/${locale}/tests/create`)}>
          <Plus className="mr-2 h-4 w-4" />
          Создать тест
        </Button>
      </div>

      {tests.length > 0 ? (
        <>
          <Input
            placeholder="Поиск по названию..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="max-w-sm"
          />
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[40px]">ID</TableHead>
                  <TableHead>Название</TableHead>
                  <TableHead>Учебник</TableHead>
                  <TableHead>Назначение</TableHead>
                  <TableHead>Сложность</TableHead>
                  <TableHead>Проходной балл</TableHead>
                  <TableHead className="text-right">Действия</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((test) => (
                  <TableRow key={test.id}>
                    <TableCell>{test.id}</TableCell>
                    <TableCell>
                      <div className="max-w-[250px]">
                        <div className="font-medium truncate">{test.title}</div>
                        {test.chapter_title && (
                          <div className="text-sm text-muted-foreground truncate">
                            {test.chapter_title}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-muted-foreground truncate block max-w-[200px]">
                        {test.textbook_title || '—'}
                      </span>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{purposeLabels[test.test_purpose]}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={difficultyVariants[test.difficulty]}>
                        {difficultyLabels[test.difficulty]}
                      </Badge>
                    </TableCell>
                    <TableCell>{test.passing_score}%</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => router.push(`/${locale}/tests/${test.id}`)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        {test.school_id !== null && (
                          <>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => router.push(`/${locale}/tests/${test.id}/edit`)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleDelete(test)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
                {filtered.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                      Ничего не найдено
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <FileQuestion className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground mb-4">У вас пока нет тестов</p>
            <Button onClick={() => router.push(`/${locale}/tests/create`)}>
              <Plus className="mr-2 h-4 w-4" />
              Создать первый тест
            </Button>
          </CardContent>
        </Card>
      )}

      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Удалить тест?</DialogTitle>
            <DialogDescription>
              Вы уверены, что хотите удалить тест &quot;{testToDelete?.title}&quot;?
              Все вопросы будут удалены.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              Отмена
            </Button>
            <Button variant="destructive" onClick={confirmDelete}>
              Удалить
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
