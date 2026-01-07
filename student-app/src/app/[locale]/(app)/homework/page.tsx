'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { ClipboardList, Loader2 } from 'lucide-react';
import { useMyHomework } from '@/lib/hooks/use-homework';
import { StudentHomeworkStatus } from '@/lib/api/homework';
import { HomeworkCard } from '@/components/homework';
import { cn } from '@/lib/utils';

type FilterTab = 'active' | 'completed';

export default function HomeworkListPage() {
  const t = useTranslations('homework');
  const [activeTab, setActiveTab] = useState<FilterTab>('active');

  const { data: homework, isLoading, error } = useMyHomework();

  // Filter homework based on tab
  const filteredHomework = homework?.filter((hw) => {
    if (activeTab === 'active') {
      return (
        hw.my_status === StudentHomeworkStatus.ASSIGNED ||
        hw.my_status === StudentHomeworkStatus.IN_PROGRESS ||
        hw.my_status === StudentHomeworkStatus.RETURNED
      );
    }
    return (
      hw.my_status === StudentHomeworkStatus.SUBMITTED ||
      hw.my_status === StudentHomeworkStatus.GRADED
    );
  });

  // Sort: overdue first, then by due_date
  const sortedHomework = filteredHomework?.sort((a, b) => {
    // Overdue first
    if (a.is_overdue && !b.is_overdue) return -1;
    if (!a.is_overdue && b.is_overdue) return 1;
    // Then by due_date (closest first)
    return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
  });

  return (
    <div className="mx-auto max-w-4xl px-4 py-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{t('title')}</h1>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab('active')}
          className={cn(
            'px-4 py-2 rounded-full text-sm font-medium transition-colors',
            activeTab === 'active'
              ? 'bg-primary text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          )}
        >
          {t('activeTab')}
        </button>
        <button
          onClick={() => setActiveTab('completed')}
          className={cn(
            'px-4 py-2 rounded-full text-sm font-medium transition-colors',
            activeTab === 'completed'
              ? 'bg-primary text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          )}
        >
          {t('completedTab')}
        </button>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center h-64">
          <Loader2 className="w-8 h-8 text-primary animate-spin mb-4" />
          <p className="text-gray-500">{t('loading')}</p>
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <p className="text-red-500">{t('error')}</p>
        </div>
      ) : sortedHomework?.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mb-4">
            <ClipboardList className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-1">
            {activeTab === 'active' ? t('noActiveHomework') : t('noCompletedHomework')}
          </h3>
          <p className="text-gray-500">{t('noHomeworkDesc')}</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {sortedHomework?.map((hw) => (
            <HomeworkCard key={hw.id} homework={hw} />
          ))}
        </div>
      )}
    </div>
  );
}
