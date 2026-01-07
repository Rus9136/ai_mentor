'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import Link from 'next/link';
import { useLocale } from 'next-intl';
import { Plus, Loader2, ClipboardList } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { HomeworkCard } from '@/components/homework';
import { useHomeworkList } from '@/lib/hooks/use-homework';
import { HomeworkStatus } from '@/types/homework';

export default function HomeworkListPage() {
  const t = useTranslations('homework');
  const locale = useLocale();

  const [statusFilter, setStatusFilter] = useState<HomeworkStatus | 'all'>('all');

  const { data: homework, isLoading, error } = useHomeworkList(
    statusFilter === 'all' ? undefined : { status: statusFilter }
  );

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

      {/* Homework Grid */}
      {homework && homework.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {homework.map((hw) => (
            <HomeworkCard key={hw.id} homework={hw} />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <ClipboardList className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium mb-1">{t('noHomework')}</h3>
          <p className="text-muted-foreground mb-4">{t('createFirst')}</p>
          <Link href={`/${locale}/homework/create`}>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              {t('create')}
            </Button>
          </Link>
        </div>
      )}
    </div>
  );
}
