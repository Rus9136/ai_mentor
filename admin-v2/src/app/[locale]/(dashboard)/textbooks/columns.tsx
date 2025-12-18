'use client';

import { type ColumnDef } from '@tanstack/react-table';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import { BookOpen, CheckCircle, XCircle, Globe, Building2 } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { DataTableColumnHeader, DataTableRowActions } from '@/components/data-table';
import type { Textbook } from '@/types';

interface ColumnsProps {
  onView: (textbook: Textbook) => void;
  onEdit: (textbook: Textbook) => void;
  onDelete: (textbook: Textbook) => void;
  onStructure: (textbook: Textbook) => void;
}

export function getColumns({
  onView,
  onEdit,
  onDelete,
  onStructure,
}: ColumnsProps): ColumnDef<Textbook>[] {
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
        <div onClick={(e) => e.stopPropagation()}>
          <Checkbox
            checked={row.getIsSelected()}
            onCheckedChange={(value) => row.toggleSelected(!!value)}
            aria-label="Выбрать строку"
          />
        </div>
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
      accessorKey: 'title',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Название" />
      ),
      cell: ({ row }) => {
        const textbook = row.original;
        return (
          <div className="flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-muted-foreground" />
            <div>
              <div className="max-w-[300px] truncate font-medium">
                {row.getValue('title')}
              </div>
              {textbook.author && (
                <div className="text-xs text-muted-foreground">
                  {textbook.author}
                </div>
              )}
            </div>
          </div>
        );
      },
    },
    {
      accessorKey: 'subject',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Предмет" />
      ),
      cell: ({ row }) => (
        <Badge variant="outline">{row.getValue('subject')}</Badge>
      ),
    },
    {
      accessorKey: 'grade_level',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Класс" />
      ),
      cell: ({ row }) => (
        <Badge variant="secondary">{row.getValue('grade_level')} класс</Badge>
      ),
    },
    {
      accessorKey: 'school_id',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Тип" />
      ),
      cell: ({ row }) => {
        const schoolId = row.getValue('school_id') as number | null;
        return schoolId === null ? (
          <Badge variant="default">
            <Globe className="mr-1 h-3 w-3" />
            Глобальный
          </Badge>
        ) : (
          <Badge variant="outline">
            <Building2 className="mr-1 h-3 w-3" />
            Школьный
          </Badge>
        );
      },
      filterFn: (row, id, value) => {
        const schoolId = row.getValue(id) as number | null;
        if (value.includes('global')) return schoolId === null;
        if (value.includes('school')) return schoolId !== null;
        return true;
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
        return value.includes(String(row.getValue(id)));
      },
    },
    {
      accessorKey: 'version',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Версия" />
      ),
      cell: ({ row }) => (
        <span className="text-muted-foreground">v{row.getValue('version')}</span>
      ),
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
        const textbook = row.original;
        return (
          <div onClick={(e) => e.stopPropagation()}>
            <DataTableRowActions
              onView={() => onView(textbook)}
              onEdit={() => onEdit(textbook)}
              onDelete={() => onDelete(textbook)}
            >
              <button
                onClick={() => onStructure(textbook)}
                className="relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-accent hover:text-accent-foreground w-full"
              >
                <BookOpen className="mr-2 h-4 w-4" />
                Структура
              </button>
            </DataTableRowActions>
          </div>
        );
      },
    },
  ];
}
