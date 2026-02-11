'use client';

import { useState, useMemo } from 'react';
import { useTranslations } from 'next-intl';
import Link from 'next/link';
import { useLocale } from 'next-intl';
import { Plus, Loader2, ClipboardList } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { HomeworkTable, HomeworkFilters, type SortField, type SortOrder } from '@/components/homework';
import { useHomeworkList } from '@/lib/hooks/use-homework';
import { useClasses } from '@/lib/hooks/use-teacher-data';
import { HomeworkStatus, type HomeworkListResponse } from '@/types/homework';

export default function HomeworkListPage() {
  const t = useTranslations('homework');
  const locale = useLocale();

  // Filters state
  const [statusFilter, setStatusFilter] = useState<HomeworkStatus | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedClassId, setSelectedClassId] = useState<number | null>(null);
  const [sortField, setSortField] = useState<SortField>('due_date');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  // Data fetching
  const { data: classes = [], isLoading: classesLoading } = useClasses();
  const { data: homework, isLoading, error } = useHomeworkList(
    statusFilter === 'all'
      ? selectedClassId ? { class_id: selectedClassId } : undefined
      : selectedClassId
        ? { status: statusFilter, class_id: selectedClassId }
        : { status: statusFilter }
  );

  // Client-side filtering and sorting
  const filteredAndSortedHomework = useMemo(() => {
    if (!homework) return [];

    let result = [...homework];

    // Search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim();
      result = result.filter((hw) =>
        hw.title.toLowerCase().includes(query)
      );
    }

    // Sort
    result.sort((a, b) => {
      let comparison = 0;

      switch (sortField) {
        case 'due_date':
          comparison = new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
          break;
        case 'created_at':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
        case 'title':
          comparison = a.title.localeCompare(b.title, locale);
          break;
      }

      return sortOrder === 'asc' ? comparison : -comparison;
    });

    return result;
  }, [homework, searchQuery, sortField, sortOrder, locale]);

  const handleSortChange = (field: SortField, order: SortOrder) => {
    setSortField(field);
    setSortOrder(order);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-destructive">{t('errors.loadFailed')}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t('title')}</h1>
        <Link href={`/${locale}/homework/create`}>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            {t('create')}
          </Button>
        </Link>
      </div>

      {/* Tabs Filter */}
      <Tabs
        value={statusFilter}
        onValueChange={(v) => setStatusFilter(v as HomeworkStatus | 'all')}
      >
        <TabsList>
          <TabsTrigger value="all">{t('tabs.all')}</TabsTrigger>
          <TabsTrigger value={HomeworkStatus.DRAFT}>{t('tabs.draft')}</TabsTrigger>
          <TabsTrigger value={HomeworkStatus.PUBLISHED}>{t('tabs.published')}</TabsTrigger>
          <TabsTrigger value={HomeworkStatus.CLOSED}>{t('tabs.closed')}</TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Filters */}
      <HomeworkFilters
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        selectedClassId={selectedClassId}
        onClassChange={setSelectedClassId}
        classes={classes}
        sortField={sortField}
        sortOrder={sortOrder}
        onSortChange={handleSortChange}
      />

      {/* Homework Table */}
      {filteredAndSortedHomework.length > 0 ? (
        <HomeworkTable homework={filteredAndSortedHomework} />
      ) : (
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <ClipboardList className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium mb-1">
            {searchQuery ? t('noSearchResults') : t('noHomework')}
          </h3>
          <p className="text-muted-foreground mb-4">
            {searchQuery ? t('tryDifferentSearch') : t('createFirst')}
          </p>
          {!searchQuery && (
            <Link href={`/${locale}/homework/create`}>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                {t('create')}
              </Button>
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
