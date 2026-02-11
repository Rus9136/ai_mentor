'use client';

import { useTranslations } from 'next-intl';
import { Search, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import type { TeacherClassResponse } from '@/lib/api/teachers';

export type SortField = 'due_date' | 'created_at' | 'title';
export type SortOrder = 'asc' | 'desc';

interface HomeworkFiltersProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  selectedClassId: number | null;
  onClassChange: (classId: number | null) => void;
  classes: TeacherClassResponse[];
  sortField: SortField;
  sortOrder: SortOrder;
  onSortChange: (field: SortField, order: SortOrder) => void;
}

export function HomeworkFilters({
  searchQuery,
  onSearchChange,
  selectedClassId,
  onClassChange,
  classes,
  sortField,
  sortOrder,
  onSortChange,
}: HomeworkFiltersProps) {
  const t = useTranslations('homework');

  const handleSortClick = (field: SortField) => {
    if (sortField === field) {
      onSortChange(field, sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      onSortChange(field, 'desc');
    }
  };

  const SortIcon = sortOrder === 'asc' ? ArrowUp : ArrowDown;

  return (
    <div className="flex flex-col sm:flex-row gap-3">
      {/* Search */}
      <div className="relative flex-1 max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder={t('filters.searchPlaceholder')}
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-9"
        />
      </div>

      {/* Class filter */}
      <Select
        value={selectedClassId?.toString() ?? 'all'}
        onValueChange={(value) => onClassChange(value === 'all' ? null : Number(value))}
      >
        <SelectTrigger className="w-full sm:w-[180px]">
          <SelectValue placeholder={t('filters.allClasses')} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">{t('filters.allClasses')}</SelectItem>
          {classes.map((cls) => (
            <SelectItem key={cls.id} value={cls.id.toString()}>
              {cls.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Sort */}
      <Select
        value={sortField}
        onValueChange={(value) => onSortChange(value as SortField, sortOrder)}
      >
        <SelectTrigger className="w-full sm:w-[160px]">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="due_date">{t('filters.sortByDueDate')}</SelectItem>
          <SelectItem value="created_at">{t('filters.sortByCreated')}</SelectItem>
          <SelectItem value="title">{t('filters.sortByTitle')}</SelectItem>
        </SelectContent>
      </Select>

      {/* Sort order toggle */}
      <Button
        variant="outline"
        size="icon"
        onClick={() => handleSortClick(sortField)}
        title={sortOrder === 'asc' ? t('filters.ascending') : t('filters.descending')}
      >
        <SortIcon className="h-4 w-4" />
      </Button>
    </div>
  );
}
