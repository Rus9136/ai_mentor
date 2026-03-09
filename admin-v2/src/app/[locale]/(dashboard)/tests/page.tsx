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
import { useSubjects } from '@/lib/hooks/use-goso';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { Test } from '@/types';
import { getColumns } from './columns';

const GRADES = [5, 6, 7, 8, 9, 10, 11];

export default function TestsPage() {
  const t = useTranslations('tests');
  const router = useRouter();
  const locale = 'ru';

  const { data: tests = [], isLoading } = useTests(false);
  const deleteTest = useDeleteTest(false);

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [testToDelete, setTestToDelete] = useState<Test | null>(null);

  // Фильтры
  const [selectedSubjectId, setSelectedSubjectId] = useState<number | null>(null);
  const [selectedGrade, setSelectedGrade] = useState<number | null>(null);
  const [selectedTextbookId, setSelectedTextbookId] = useState<number | null>(null);
  const [selectedChapterId, setSelectedChapterId] = useState<number | null>(null);

  // Загрузка данных
  const { data: subjects = [] } = useSubjects();
  const { data: allTextbooks = [] } = useTextbooks(false);
  const { data: chapters = [] } = useChapters(
    selectedTextbookId || 0,
    false,
    !!selectedTextbookId
  );

  // Фильтруем учебники по предмету и классу
  const filteredTextbooks = useMemo(() => {
    return allTextbooks.filter((tb) => {
      if (selectedSubjectId !== null && tb.subject_id !== selectedSubjectId) return false;
      if (selectedGrade !== null && tb.grade_level !== selectedGrade) return false;
      return true;
    });
  }, [allTextbooks, selectedSubjectId, selectedGrade]);

  // Каскадный сброс
  useEffect(() => {
    setSelectedTextbookId(null);
    setSelectedChapterId(null);
  }, [selectedSubjectId, selectedGrade]);

  useEffect(() => {
    setSelectedChapterId(null);
  }, [selectedTextbookId]);

  // Собираем set textbook_id из отфильтрованных учебников для фильтра тестов
  const filteredTests = useMemo(() => {
    const textbookIds = selectedSubjectId !== null || selectedGrade !== null
      ? new Set(filteredTextbooks.map((tb) => tb.id))
      : null;

    return tests.filter((test) => {
      if (textbookIds !== null && !textbookIds.has(test.textbook_id ?? 0)) return false;
      if (selectedTextbookId !== null && test.textbook_id !== selectedTextbookId) return false;
      if (selectedChapterId !== null && test.chapter_id !== selectedChapterId) return false;
      return true;
    });
  }, [tests, filteredTextbooks, selectedSubjectId, selectedGrade, selectedTextbookId, selectedChapterId]);

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

  const filtersToolbar = (
    <div className="flex items-center gap-2 flex-wrap">
      <Select
        value={selectedSubjectId ? String(selectedSubjectId) : 'all'}
        onValueChange={(v) => setSelectedSubjectId(v === 'all' ? null : parseInt(v))}
      >
        <SelectTrigger className="h-8 w-[180px]">
          <SelectValue placeholder="Все предметы" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Все предметы</SelectItem>
          {subjects.filter((s) => s.is_active).map((s) => (
            <SelectItem key={s.id} value={String(s.id)}>
              {s.name_ru}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={selectedGrade ? String(selectedGrade) : 'all'}
        onValueChange={(v) => setSelectedGrade(v === 'all' ? null : parseInt(v))}
      >
        <SelectTrigger className="h-8 w-[130px]">
          <SelectValue placeholder="Все классы" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Все классы</SelectItem>
          {GRADES.map((g) => (
            <SelectItem key={g} value={String(g)}>
              {g} класс
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={selectedTextbookId ? String(selectedTextbookId) : 'all'}
        onValueChange={(v) => setSelectedTextbookId(v === 'all' ? null : parseInt(v))}
      >
        <SelectTrigger className="h-8 w-[200px]">
          <SelectValue placeholder="Все учебники" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Все учебники</SelectItem>
          {filteredTextbooks.map((tb) => (
            <SelectItem key={tb.id} value={String(tb.id)}>
              {tb.title}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={selectedChapterId ? String(selectedChapterId) : 'all'}
        onValueChange={(v) => setSelectedChapterId(v === 'all' ? null : parseInt(v))}
        disabled={!selectedTextbookId}
      >
        <SelectTrigger className="h-8 w-[200px]">
          <SelectValue placeholder={!selectedTextbookId ? 'Выберите учебник' : 'Все главы'} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Все главы</SelectItem>
          {chapters.map((ch) => (
            <SelectItem key={ch.id} value={String(ch.id)}>
              {ch.number}. {ch.title}
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
          toolbar={filtersToolbar}
          onRowClick={handleView}
          defaultPageSize={50}
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
