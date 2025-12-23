'use client';

import { type ColumnDef } from '@tanstack/react-table';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import {
  ClipboardList,
  CheckCircle,
  XCircle,
  Globe,
  Building2,
  Timer,
  Target,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { DataTableColumnHeader, DataTableRowActions } from '@/components/data-table';
import type { Test, TestPurpose, DifficultyLevel } from '@/types';

interface ColumnsProps {
  onView: (test: Test) => void;
  onEdit: (test: Test) => void;
  onDelete: (test: Test) => void;
  onQuestions: (test: Test) => void;
}

const PURPOSE_LABELS: Record<TestPurpose, string> = {
  diagnostic: 'Диагностический',
  formative: 'Формативный',
  summative: 'Суммативный',
  practice: 'Практический',
};

const DIFFICULTY_LABELS: Record<DifficultyLevel, string> = {
  easy: 'Легкий',
  medium: 'Средний',
  hard: 'Сложный',
};

const DIFFICULTY_COLORS: Record<DifficultyLevel, string> = {
  easy: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  hard: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
};

export function getColumns({
  onView,
  onEdit,
  onDelete,
  onQuestions,
}: ColumnsProps): ColumnDef<Test>[] {
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
      accessorKey: 'title',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Название" />
      ),
      cell: ({ row }) => {
        const test = row.original;
        return (
          <div className="flex items-center gap-2">
            <ClipboardList className="h-4 w-4 text-muted-foreground" />
            <div>
              <div className="max-w-[300px] truncate font-medium">
                {row.getValue('title')}
              </div>
              {test.description && (
                <div className="text-xs text-muted-foreground max-w-[300px] truncate">
                  {test.description}
                </div>
              )}
            </div>
          </div>
        );
      },
    },
    {
      accessorKey: 'textbook_id',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Учебник" />
      ),
      cell: ({ row }) => {
        const textbookId = row.getValue('textbook_id') as number | null;
        return textbookId ? (
          <Badge variant="outline">ID: {textbookId}</Badge>
        ) : (
          <span className="text-muted-foreground">—</span>
        );
      },
      filterFn: (row, id, value) => {
        if (!value) return true;
        return row.getValue(id) === value;
      },
    },
    {
      accessorKey: 'chapter_id',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Глава" />
      ),
      cell: ({ row }) => {
        const chapterId = row.getValue('chapter_id') as number | null;
        return chapterId ? (
          <Badge variant="outline">ID: {chapterId}</Badge>
        ) : (
          <span className="text-muted-foreground">—</span>
        );
      },
      filterFn: (row, id, value) => {
        if (!value) return true;
        return row.getValue(id) === value;
      },
    },
    {
      accessorKey: 'test_purpose',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Назначение" />
      ),
      cell: ({ row }) => {
        const purpose = row.getValue('test_purpose') as TestPurpose;
        return <Badge variant="outline">{PURPOSE_LABELS[purpose]}</Badge>;
      },
      filterFn: (row, id, value) => {
        return value.includes(row.getValue(id));
      },
    },
    {
      accessorKey: 'difficulty',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Сложность" />
      ),
      cell: ({ row }) => {
        const difficulty = row.getValue('difficulty') as DifficultyLevel;
        return (
          <Badge className={DIFFICULTY_COLORS[difficulty]}>
            {DIFFICULTY_LABELS[difficulty]}
          </Badge>
        );
      },
      filterFn: (row, id, value) => {
        return value.includes(row.getValue(id));
      },
    },
    {
      accessorKey: 'time_limit',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Время" />
      ),
      cell: ({ row }) => {
        const timeLimit = row.getValue('time_limit') as number | null;
        return timeLimit ? (
          <div className="flex items-center gap-1 text-muted-foreground">
            <Timer className="h-3 w-3" />
            {timeLimit} мин
          </div>
        ) : (
          <span className="text-muted-foreground">—</span>
        );
      },
    },
    {
      accessorKey: 'passing_score',
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Проходной" />
      ),
      cell: ({ row }) => {
        const score = row.getValue('passing_score') as number;
        return (
          <div className="flex items-center gap-1">
            <Target className="h-3 w-3 text-muted-foreground" />
            {score}%
          </div>
        );
      },
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
        const test = row.original;
        return (
          <DataTableRowActions
            onView={() => onView(test)}
            onEdit={() => onEdit(test)}
            onDelete={() => onDelete(test)}
          >
            <button
              onClick={() => onQuestions(test)}
              className="relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-accent hover:text-accent-foreground w-full"
            >
              <ClipboardList className="mr-2 h-4 w-4" />
              Вопросы
            </button>
          </DataTableRowActions>
        );
      },
    },
  ];
}
