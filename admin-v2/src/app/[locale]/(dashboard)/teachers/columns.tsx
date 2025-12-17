'use client';

import { type ColumnDef } from '@tanstack/react-table';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import { CheckCircle, XCircle } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { DataTableColumnHeader, DataTableRowActions } from '@/components/data-table';
import type { Teacher } from '@/types';

interface ColumnsProps {
  onView: (teacher: Teacher) => void;
  onEdit: (teacher: Teacher) => void;
  onDelete: (teacher: Teacher) => void;
}

export function getColumns({
  onView,
  onEdit,
  onDelete,
}: ColumnsProps): ColumnDef<Teacher>[] {
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
        const teacher = row.original;
        const user = teacher.user;
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
        const teacher = row.original;
        const user = teacher.user;
        const fullName = user
          ? `${user.last_name || ''} ${user.first_name || ''} ${user.middle_name || ''}`.toLowerCase()
          : '';
        return fullName.includes(value.toLowerCase());
      },
    },
    {
      accessorKey: 'subject',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Предмет" />
      ),
      cell: ({ row }) => {
        const subject = row.getValue('subject') as string | null;
        return subject ? (
          <Badge variant="outline">{subject}</Badge>
        ) : (
          <span className="text-muted-foreground">—</span>
        );
      },
    },
    {
      accessorKey: 'teacher_code',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Код" />
      ),
      cell: ({ row }) => {
        const code = row.getValue('teacher_code') as string | undefined;
        return code ? (
          <code className="rounded bg-muted px-1.5 py-0.5 text-sm">{code}</code>
        ) : (
          <span className="text-muted-foreground">—</span>
        );
      },
    },
    {
      id: 'classesCount',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Классы" />
      ),
      cell: ({ row }) => {
        const classes = row.original.classes || [];
        return (
          <Badge variant="secondary">
            {classes.length} кл.
          </Badge>
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
      filterFn: (row, id, value) => {
        const isActive = row.original.user?.is_active ?? true;
        return value.includes(String(isActive));
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
        const teacher = row.original;
        return (
          <DataTableRowActions
            onView={() => onView(teacher)}
            onEdit={() => onEdit(teacher)}
            onDelete={() => onDelete(teacher)}
          />
        );
      },
    },
  ];
}
