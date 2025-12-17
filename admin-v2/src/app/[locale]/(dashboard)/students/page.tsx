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
import { useStudents, useDeleteStudent } from '@/lib/hooks';
import type { Student } from '@/types';
import { getColumns } from './columns';

export default function StudentsPage() {
  const t = useTranslations('students');
  const router = useRouter();
  const locale = 'ru';

  const { data: students = [], isLoading } = useStudents();
  const deleteStudent = useDeleteStudent();

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [studentToDelete, setStudentToDelete] = useState<Student | null>(null);

  const handleView = (student: Student) => {
    router.push(`/${locale}/students/${student.id}`);
  };

  const handleEdit = (student: Student) => {
    router.push(`/${locale}/students/${student.id}/edit`);
  };

  const handleDelete = (student: Student) => {
    setStudentToDelete(student);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (studentToDelete) {
      deleteStudent.mutate(studentToDelete.id);
    }
    setDeleteDialogOpen(false);
    setStudentToDelete(null);
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
      title: 'Класс',
      options: Array.from({ length: 11 }, (_, i) => ({
        label: `${i + 1} класс`,
        value: String(i + 1),
      })),
    },
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
              Управление учениками школы
            </p>
          </div>
          <Button onClick={() => router.push(`/${locale}/students/create`)}>
            <Plus className="mr-2 h-4 w-4" />
            {t('create')}
          </Button>
        </div>

        <DataTable
          columns={columns}
          data={students}
          isLoading={isLoading}
          searchKey="fullName"
          searchPlaceholder="Поиск по ФИО..."
          filterableColumns={filterableColumns}
        />

        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Удалить ученика?</AlertDialogTitle>
              <AlertDialogDescription>
                Вы уверены, что хотите удалить ученика{' '}
                &quot;{studentToDelete?.user?.last_name} {studentToDelete?.user?.first_name}&quot;?
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
