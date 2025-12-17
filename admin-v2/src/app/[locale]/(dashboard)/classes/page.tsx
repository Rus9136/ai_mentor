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
import { useClasses, useDeleteClass } from '@/lib/hooks';
import type { SchoolClass } from '@/types';
import { getColumns } from './columns';

export default function ClassesPage() {
  const t = useTranslations('classes');
  const router = useRouter();
  const locale = 'ru';

  const { data: classes = [], isLoading } = useClasses();
  const deleteClass = useDeleteClass();

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [classToDelete, setClassToDelete] = useState<SchoolClass | null>(null);

  const handleView = (schoolClass: SchoolClass) => {
    router.push(`/${locale}/classes/${schoolClass.id}`);
  };

  const handleEdit = (schoolClass: SchoolClass) => {
    router.push(`/${locale}/classes/${schoolClass.id}/edit`);
  };

  const handleDelete = (schoolClass: SchoolClass) => {
    setClassToDelete(schoolClass);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (classToDelete) {
      deleteClass.mutate(classToDelete.id);
    }
    setDeleteDialogOpen(false);
    setClassToDelete(null);
  };

  const columns = useMemo(
    () =>
      getColumns({
        onView: handleView,
        onEdit: handleEdit,
        onDelete: handleDelete,
      }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  const filterableColumns = [
    {
      id: 'grade_level',
      title: 'Параллель',
      options: Array.from({ length: 11 }, (_, i) => ({
        label: `${i + 1} класс`,
        value: String(i + 1),
      })),
    },
  ];

  return (
    <RoleGuard allowedRoles={['admin']}>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{t('title')}</h1>
            <p className="text-muted-foreground">
              Управление классами школы
            </p>
          </div>
          <Button onClick={() => router.push(`/${locale}/classes/create`)}>
            <Plus className="mr-2 h-4 w-4" />
            {t('create')}
          </Button>
        </div>

        <DataTable
          columns={columns}
          data={classes}
          isLoading={isLoading}
          searchKey="name"
          searchPlaceholder="Поиск по названию..."
          filterableColumns={filterableColumns}
        />

        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Удалить класс?</AlertDialogTitle>
              <AlertDialogDescription>
                Вы уверены, что хотите удалить класс &quot;{classToDelete?.name}&quot;?
                Ученики и учителя будут отвязаны от класса.
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
