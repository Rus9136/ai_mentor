'use client';

import { useMemo, useState } from 'react';
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
import { useTextbooks, useDeleteTextbook } from '@/lib/hooks/use-textbooks';
import type { Textbook } from '@/types';
import { getColumns } from './columns';

export default function TextbooksPage() {
  const t = useTranslations('textbooks');
  const router = useRouter();
  const locale = 'ru';

  const { data: textbooks = [], isLoading } = useTextbooks(false); // global textbooks
  const deleteTextbook = useDeleteTextbook(false);

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [textbookToDelete, setTextbookToDelete] = useState<Textbook | null>(null);

  const handleView = (textbook: Textbook) => {
    router.push(`/${locale}/textbooks/${textbook.id}`);
  };

  const handleEdit = (textbook: Textbook) => {
    router.push(`/${locale}/textbooks/${textbook.id}/edit`);
  };

  const handleDelete = (textbook: Textbook) => {
    setTextbookToDelete(textbook);
    setDeleteDialogOpen(true);
  };

  const handleStructure = (textbook: Textbook) => {
    router.push(`/${locale}/textbooks/${textbook.id}/structure`);
  };

  const confirmDelete = () => {
    if (textbookToDelete) {
      deleteTextbook.mutate(textbookToDelete.id);
    }
    setDeleteDialogOpen(false);
    setTextbookToDelete(null);
  };

  const columns = useMemo(
    () =>
      getColumns({
        onView: handleView,
        onEdit: handleEdit,
        onDelete: handleDelete,
        onStructure: handleStructure,
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
      id: 'grade_level',
      title: 'Класс',
      options: [
        { label: '7 класс', value: '7' },
        { label: '8 класс', value: '8' },
        { label: '9 класс', value: '9' },
        { label: '10 класс', value: '10' },
        { label: '11 класс', value: '11' },
      ],
    },
  ];

  return (
    <RoleGuard allowedRoles={['super_admin']}>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{t('title')}</h1>
            <p className="text-muted-foreground">
              Управление глобальными учебниками платформы
            </p>
          </div>
          <Button onClick={() => router.push(`/${locale}/textbooks/create`)}>
            <Plus className="mr-2 h-4 w-4" />
            {t('create')}
          </Button>
        </div>

        <DataTable
          columns={columns}
          data={textbooks}
          isLoading={isLoading}
          searchKey="title"
          searchPlaceholder="Поиск по названию..."
          filterableColumns={filterableColumns}
          onRowClick={handleStructure}
        />

        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Удалить учебник?</AlertDialogTitle>
              <AlertDialogDescription>
                Вы уверены, что хотите удалить учебник &quot;{textbookToDelete?.title}
                &quot;? Это действие нельзя отменить. Все главы и параграфы будут удалены.
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
