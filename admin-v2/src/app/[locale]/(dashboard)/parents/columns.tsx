'use client';

import { type ColumnDef } from '@tanstack/react-table';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import { CheckCircle, XCircle, Users } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { DataTableColumnHeader, DataTableRowActions } from '@/components/data-table';
import type { Parent } from '@/types';

interface ColumnsProps {
  onView: (parent: Parent) => void;
  onDelete: (parent: Parent) => void;
}

export function getColumns({
  onView,
  onDelete,
}: ColumnsProps): ColumnDef<Parent>[] {
  return [
    {
      id: 'select',
      header: ({ table }) => (
        <Checkbox
          checked={
            table.getIsAllPageRowsSelected() ||
            (table.getIsSomePageRowsSelected() && 'indeterminate')
          }
          onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
          aria-label="Выбрать все"
        />
      ),
      cell: ({ row }) => (
        <Checkbox
          checked={row.getIsSelected()}
          onCheckedChange={(value) => row.toggleSelected(!!value)}
          aria-label="Выбрать строку"
        />
      ),
      enableSorting: false,
      enableHiding: false,
    },
    {
      accessorKey: 'id',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="ID" />
      ),
      cell: ({ row }) => <div className="w-[40px]">{row.getValue('id')}</div>,
    },
    {
      id: 'fullName',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="ФИО" />
      ),
      cell: ({ row }) => {
        const parent = row.original;
        const user = parent.user;
        const fullName = user
          ? `${user.last_name || ''} ${user.first_name || ''} ${user.middle_name || ''}`.trim()
          : '—';
        return (
          <div className="max-w-[250px]">
            <div className="font-medium truncate">{fullName}</div>
            {user?.email && (
              <div className="text-sm text-muted-foreground truncate">{user.email}</div>
            )}
          </div>
        );
      },
      filterFn: (row, id, value) => {
        const parent = row.original;
        const user = parent.user;
        const fullName = user
          ? `${user.last_name || ''} ${user.first_name || ''} ${user.middle_name || ''}`.toLowerCase()
          : '';
        return fullName.includes(value.toLowerCase());
      },
    },
    {
      id: 'phone',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Телефон" />
      ),
      cell: ({ row }) => {
        const phone = row.original.user?.phone;
        return phone || <span className="text-muted-foreground">—</span>;
      },
    },
    {
      id: 'childrenCount',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Дети" />
      ),
      cell: ({ row }) => {
        const children = row.original.children || [];
        return (
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-muted-foreground" />
            <Badge variant="secondary">
              {children.length}
            </Badge>
          </div>
        );
      },
    },
    {
      id: 'status',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Статус" />
      ),
      cell: ({ row }) => {
        const isActive = row.original.user?.is_active ?? true;
        return (
          <Badge variant={isActive ? 'default' : 'secondary'}>
            {isActive ? (
              <>
                <CheckCircle className="mr-1 h-3 w-3" />
                Активен
              </>
            ) : (
              <>
                <XCircle className="mr-1 h-3 w-3" />
                Неактивен
              </>
            )}
          </Badge>
        );
      },
    },
    {
      accessorKey: 'created_at',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Добавлен" />
      ),
      cell: ({ row }) => {
        const date = row.getValue('created_at') as string;
        return (
          <div className="text-muted-foreground">
            {format(new Date(date), 'dd MMM yyyy', { locale: ru })}
          </div>
        );
      },
    },
    {
      id: 'actions',
      cell: ({ row }) => {
        const parent = row.original;
        return (
          <DataTableRowActions
            onView={() => onView(parent)}
            onDelete={() => onDelete(parent)}
          />
        );
      },
    },
  ];
}
