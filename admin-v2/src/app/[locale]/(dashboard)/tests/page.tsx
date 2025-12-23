'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { Plus } from 'lucide-react';

import { Button } from '@/components/ui/button';
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
import { RoleGuard } from '@/components/auth';
import { useTests, useDeleteTest } from '@/lib/hooks/use-tests';
import { useTextbooks, useChapters } from '@/lib/hooks/use-textbooks';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { Test } from '@/types';
import { getColumns } from './columns';

export default function TestsPage() {
  const t = useTranslations('tests');
  const router = useRouter();
  const locale = 'ru';

  const { data: tests = [], isLoading } = useTests(false); // global tests
  const deleteTest = useDeleteTest(false);

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [testToDelete, setTestToDelete] = useState<Test | null>(null);

  // Состояние фильтров по учебнику/главе
  const [selectedTextbookId, setSelectedTextbookId] = useState<number | null>(null);
  const [selectedChapterId, setSelectedChapterId] = useState<number | null>(null);

  // Загрузка данных для фильтров
  const { data: textbooks = [] } = useTextbooks(false);
  const { data: chapters = [] } = useChapters(
    selectedTextbookId || 0,
    false,
    !!selectedTextbookId
  );

  // Каскадный сброс главы при смене учебника
  useEffect(() => {
    setSelectedChapterId(null);
  }, [selectedTextbookId]);

  // Фильтруем тесты по учебнику и главе
  const filteredTests = useMemo(() => {
    return tests.filter((test) => {
      if (selectedTextbookId !== null && test.textbook_id !== selectedTextbookId) {
        return false;
      }
      if (selectedChapterId !== null && test.chapter_id !== selectedChapterId) {
        return false;
      }
      return true;
    });
  }, [tests, selectedTextbookId, selectedChapterId]);

  const handleView = (test: Test) => {
    router.push(`/${locale}/tests/${test.id}`);
  };

  const handleEdit = (test: Test) => {
    router.push(`/${locale}/tests/${test.id}/edit`);
  };

  const handleDelete = (test: Test) => {
    setTestToDelete(test);
    setDeleteDialogOpen(true);
  };

  const handleQuestions = (test: Test) => {
    router.push(`/${locale}/tests/${test.id}/questions`);
  };

  const confirmDelete = () => {
    if (testToDelete) {
      deleteTest.mutate(testToDelete.id);
    }
    setDeleteDialogOpen(false);
    setTestToDelete(null);
  };

  const columns = useMemo(
    () =>
      getColumns({
        onView: handleView,
        onEdit: handleEdit,
        onDelete: handleDelete,
        onQuestions: handleQuestions,
      }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  const filterableColumns = [
    {
      id: 'is_active',
      title: 'Статус',
      options: [
        { label: 'Активные', value: 'true' },
        { label: 'Неактивные', value: 'false' },
      ],
    },
    {
      id: 'test_purpose',
      title: 'Назначение',
      options: [
        { label: 'Диагностический', value: 'diagnostic' },
        { label: 'Формативный', value: 'formative' },
        { label: 'Суммативный', value: 'summative' },
        { label: 'Практический', value: 'practice' },
      ],
    },
    {
      id: 'difficulty',
      title: 'Сложность',
      options: [
        { label: 'Легкий', value: 'easy' },
        { label: 'Средний', value: 'medium' },
        { label: 'Сложный', value: 'hard' },
      ],
    },
  ];

  const textbookChapterToolbar = (
    <div className="flex items-center gap-2">
      <Select
        value={selectedTextbookId ? String(selectedTextbookId) : 'all'}
        onValueChange={(value) => {
          setSelectedTextbookId(value === 'all' ? null : parseInt(value));
        }}
      >
        <SelectTrigger className="h-8 w-[200px]">
          <SelectValue placeholder="Все учебники" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Все учебники</SelectItem>
          {textbooks.map((textbook) => (
            <SelectItem key={textbook.id} value={String(textbook.id)}>
              {textbook.title}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={selectedChapterId ? String(selectedChapterId) : 'all'}
        onValueChange={(value) => {
          setSelectedChapterId(value === 'all' ? null : parseInt(value));
        }}
        disabled={!selectedTextbookId}
      >
        <SelectTrigger className="h-8 w-[200px]">
          <SelectValue placeholder={!selectedTextbookId ? 'Выберите учебник' : 'Все главы'} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Все главы</SelectItem>
          {chapters.map((chapter) => (
            <SelectItem key={chapter.id} value={String(chapter.id)}>
              {chapter.number}. {chapter.title}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );

  return (
    <RoleGuard allowedRoles={['super_admin']}>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{t('title')}</h1>
            <p className="text-muted-foreground">
              Управление глобальными тестами платформы
            </p>
          </div>
          <Button onClick={() => router.push(`/${locale}/tests/create`)}>
            <Plus className="mr-2 h-4 w-4" />
            {t('create')}
          </Button>
        </div>

        <DataTable
          columns={columns}
          data={filteredTests}
          isLoading={isLoading}
          searchKey="title"
          searchPlaceholder="Поиск по названию..."
          filterableColumns={filterableColumns}
          toolbar={textbookChapterToolbar}
          onRowClick={handleView}
        />

        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Удалить тест?</AlertDialogTitle>
              <AlertDialogDescription>
                Вы уверены, что хотите удалить тест &quot;{testToDelete?.title}
                &quot;? Это действие нельзя отменить. Все вопросы будут удалены.
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
