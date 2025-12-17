'use client';

import { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { Plus, Ban, CheckCircle } from 'lucide-react';

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
import {
  useSchools,
  useDeleteSchool,
  useBlockSchool,
  useUnblockSchool,
  useBulkBlockSchools,
  useBulkUnblockSchools,
} from '@/lib/hooks/use-schools';
import type { School } from '@/types';
import { getColumns } from './columns';

export default function SchoolsPage() {
  const t = useTranslations('schools');
  const router = useRouter();
  const locale = 'ru'; // TODO: get from params

  const { data: schools = [], isLoading } = useSchools();
  const deleteSchool = useDeleteSchool();
  const blockSchool = useBlockSchool();
  const unblockSchool = useUnblockSchool();
  const bulkBlock = useBulkBlockSchools();
  const bulkUnblock = useBulkUnblockSchools();

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [schoolToDelete, setSchoolToDelete] = useState<School | null>(null);

  const handleView = (school: School) => {
    router.push(`/${locale}/schools/${school.id}`);
  };

  const handleEdit = (school: School) => {
    router.push(`/${locale}/schools/${school.id}/edit`);
  };

  const handleDelete = (school: School) => {
    setSchoolToDelete(school);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (schoolToDelete) {
      deleteSchool.mutate(schoolToDelete.id);
    }
    setDeleteDialogOpen(false);
    setSchoolToDelete(null);
  };

  const handleBlock = (school: School) => {
    blockSchool.mutate(school.id);
  };

  const handleUnblock = (school: School) => {
    unblockSchool.mutate(school.id);
  };

  const columns = useMemo(
    () =>
      getColumns({
        onView: handleView,
        onEdit: handleEdit,
        onDelete: handleDelete,
        onBlock: handleBlock,
        onUnblock: handleUnblock,
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
        { label: 'Заблокированные', value: 'false' },
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
              Управление школами на платформе
            </p>
          </div>
          <Button onClick={() => router.push(`/${locale}/schools/create`)}>
            <Plus className="mr-2 h-4 w-4" />
            {t('create')}
          </Button>
        </div>

        <DataTable
          columns={columns}
          data={schools}
          isLoading={isLoading}
          searchKey="name"
          searchPlaceholder="Поиск по названию..."
          filterableColumns={filterableColumns}
          toolbar={
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  // TODO: implement bulk actions with selected rows
                }}
                disabled
              >
                <Ban className="mr-2 h-4 w-4" />
                Заблокировать выбранные
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  // TODO: implement bulk actions with selected rows
                }}
                disabled
              >
                <CheckCircle className="mr-2 h-4 w-4" />
                Разблокировать выбранные
              </Button>
            </>
          }
        />

        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Удалить школу?</AlertDialogTitle>
              <AlertDialogDescription>
                Вы уверены, что хотите удалить школу &quot;{schoolToDelete?.name}
                &quot;? Это действие нельзя отменить.
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
