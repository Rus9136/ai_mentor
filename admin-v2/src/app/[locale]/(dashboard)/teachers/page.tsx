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
import { useTeachers, useDeleteTeacher } from '@/lib/hooks';
import type { Teacher } from '@/types';
import { getColumns } from './columns';

export default function TeachersPage() {
  const t = useTranslations('teachers');
  const router = useRouter();
  const locale = 'ru';

  const { data: teachers = [], isLoading } = useTeachers();
  const deleteTeacher = useDeleteTeacher();

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [teacherToDelete, setTeacherToDelete] = useState<Teacher | null>(null);

  const handleView = (teacher: Teacher) => {
    router.push(`/${locale}/teachers/${teacher.id}`);
  };

  const handleEdit = (teacher: Teacher) => {
    router.push(`/${locale}/teachers/${teacher.id}/edit`);
  };

  const handleDelete = (teacher: Teacher) => {
    setTeacherToDelete(teacher);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (teacherToDelete) {
      deleteTeacher.mutate(teacherToDelete.id);
    }
    setDeleteDialogOpen(false);
    setTeacherToDelete(null);
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
      id: 'status',
      title: 'Статус',
      options: [
        { label: 'Активные', value: 'true' },
        { label: 'Неактивные', value: 'false' },
      ],
    },
  ];

  return (
    <RoleGuard allowedRoles={['admin']}>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{t('title')}</h1>
            <p className="text-muted-foreground">
              Управление учителями школы
            </p>
          </div>
          <Button onClick={() => router.push(`/${locale}/teachers/create`)}>
            <Plus className="mr-2 h-4 w-4" />
            {t('create')}
          </Button>
        </div>

        <DataTable
          columns={columns}
          data={teachers}
          isLoading={isLoading}
          searchKey="fullName"
          searchPlaceholder="Поиск по ФИО..."
          filterableColumns={filterableColumns}
        />

        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Удалить учителя?</AlertDialogTitle>
              <AlertDialogDescription>
                Вы уверены, что хотите удалить учителя{' '}
                &quot;{teacherToDelete?.user?.last_name} {teacherToDelete?.user?.first_name}&quot;?
                Это действие нельзя отменить.
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
