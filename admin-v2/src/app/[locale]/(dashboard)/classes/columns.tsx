'use client';

import { type ColumnDef } from '@tanstack/react-table';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import { Users, GraduationCap } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { DataTableColumnHeader, DataTableRowActions } from '@/components/data-table';
import type { SchoolClass } from '@/types';

interface ColumnsProps {
  onView: (schoolClass: SchoolClass) => void;
  onEdit: (schoolClass: SchoolClass) => void;
  onDelete: (schoolClass: SchoolClass) => void;
}

export function getColumns({
  onView,
  onEdit,
  onDelete,
}: ColumnsProps): ColumnDef<SchoolClass>[] {
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
        <div className="font-medium">{row.getValue('name')}</div>
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
      accessorKey: 'grade_level',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Параллель" />
      ),
      cell: ({ row }) => (
        <Badge variant="outline">{row.getValue('grade_level')} класс</Badge>
      ),
      filterFn: (row, id, value) => {
        return value.includes(String(row.getValue(id)));
      },
    },
    {
      accessorKey: 'academic_year',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Учебный год" />
      ),
      cell: ({ row }) => row.getValue('academic_year'),
    },
    {
      id: 'studentsCount',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Учеников" />
      ),
      cell: ({ row }) => {
        const count = row.original.students_count ?? row.original.students?.length ?? 0;
        return (
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-muted-foreground" />
            <span>{count}</span>
          </div>
        );
      },
    },
    {
      id: 'teachersCount',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Учителей" />
      ),
      cell: ({ row }) => {
        const count = row.original.teachers_count ?? row.original.teachers?.length ?? 0;
        return (
          <div className="flex items-center gap-2">
            <GraduationCap className="h-4 w-4 text-muted-foreground" />
            <span>{count}</span>
          </div>
        );
      },
    },
    {
      accessorKey: 'created_at',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Создан" />
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
        const schoolClass = row.original;
        return (
          <DataTableRowActions
            onView={() => onView(schoolClass)}
            onEdit={() => onEdit(schoolClass)}
            onDelete={() => onDelete(schoolClass)}
          />
        );
      },
    },
  ];
}
