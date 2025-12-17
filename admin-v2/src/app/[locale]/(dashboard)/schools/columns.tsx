'use client';

import { type ColumnDef } from '@tanstack/react-table';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import { Ban, CheckCircle } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { DataTableColumnHeader, DataTableRowActions } from '@/components/data-table';
import type { School } from '@/types';

interface ColumnsProps {
  onView: (school: School) => void;
  onEdit: (school: School) => void;
  onDelete: (school: School) => void;
  onBlock: (school: School) => void;
  onUnblock: (school: School) => void;
}

export function getColumns({
  onView,
  onEdit,
  onDelete,
  onBlock,
  onUnblock,
}: ColumnsProps): ColumnDef<School>[] {
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
      accessorKey: 'name',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Название" />
      ),
      cell: ({ row }) => (
        <div className="max-w-[300px] truncate font-medium">
          {row.getValue('name')}
        </div>
      ),
    },
    {
      accessorKey: 'code',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Код" />
      ),
      cell: ({ row }) => (
        <code className="rounded bg-muted px-1.5 py-0.5 text-sm">
          {row.getValue('code')}
        </code>
      ),
    },
    {
      accessorKey: 'email',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Email" />
      ),
      cell: ({ row }) => {
        const email = row.getValue('email') as string | undefined;
        return email ? (
          <a
            href={`mailto:${email}`}
            className="text-primary hover:underline"
          >
            {email}
          </a>
        ) : (
          <span className="text-muted-foreground">—</span>
        );
      },
    },
    {
      accessorKey: 'is_active',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Статус" />
      ),
      cell: ({ row }) => {
        const isActive = row.getValue('is_active') as boolean;
        return (
          <Badge variant={isActive ? 'default' : 'destructive'}>
            {isActive ? (
              <>
                <CheckCircle className="mr-1 h-3 w-3" />
                Активна
              </>
            ) : (
              <>
                <Ban className="mr-1 h-3 w-3" />
                Заблокирована
              </>
            )}
          </Badge>
        );
      },
      filterFn: (row, id, value) => {
        return value.includes(String(row.getValue(id)));
      },
    },
    {
      accessorKey: 'created_at',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Создана" />
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
        const school = row.original;
        return (
          <DataTableRowActions
            onView={() => onView(school)}
            onEdit={() => onEdit(school)}
            onDelete={() => onDelete(school)}
          >
            {school.is_active ? (
              <button
                onClick={() => onBlock(school)}
                className="relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-accent hover:text-accent-foreground w-full"
              >
                <Ban className="mr-2 h-4 w-4" />
                Заблокировать
              </button>
            ) : (
              <button
                onClick={() => onUnblock(school)}
                className="relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-accent hover:text-accent-foreground w-full"
              >
                <CheckCircle className="mr-2 h-4 w-4" />
                Разблокировать
              </button>
            )}
          </DataTableRowActions>
        );
      },
    },
  ];
}
