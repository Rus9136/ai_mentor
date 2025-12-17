'use client';

import { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
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
import { useParents, useDeleteParent } from '@/lib/hooks';
import type { Parent } from '@/types';
import { getColumns } from './columns';

export default function ParentsPage() {
  const router = useRouter();
  const locale = 'ru';

  const { data: parents = [], isLoading } = useParents();
  const deleteParent = useDeleteParent();

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [parentToDelete, setParentToDelete] = useState<Parent | null>(null);

  const handleView = (parent: Parent) => {
    router.push(`/${locale}/parents/${parent.id}`);
  };

  const handleDelete = (parent: Parent) => {
    setParentToDelete(parent);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (parentToDelete) {
      deleteParent.mutate(parentToDelete.id);
    }
    setDeleteDialogOpen(false);
    setParentToDelete(null);
  };

  const columns = useMemo(
    () =>
      getColumns({
        onView: handleView,
        onDelete: handleDelete,
      }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  return (
    <RoleGuard allowedRoles={['admin']}>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Родители</h1>
            <p className="text-muted-foreground">
              Управление родителями учеников
            </p>
          </div>
          <Button onClick={() => router.push(`/${locale}/parents/create`)}>
            <Plus className="mr-2 h-4 w-4" />
            Добавить родителя
          </Button>
        </div>

        <DataTable
          columns={columns}
          data={parents}
          isLoading={isLoading}
          searchKey="fullName"
          searchPlaceholder="Поиск по ФИО..."
        />

        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Удалить родителя?</AlertDialogTitle>
              <AlertDialogDescription>
                Вы уверены, что хотите удалить{' '}
                &quot;{parentToDelete?.user?.last_name} {parentToDelete?.user?.first_name}&quot;?
                Связь с детьми будет удалена.
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
