'use client';

import { useTranslations } from 'next-intl';
import { TrendingUp, AlertCircle } from 'lucide-react';
import { MasteryOverview, ChapterMasteryDetail } from '@/lib/api/profile';

interface MasteryOverviewProps {
  data: MasteryOverview | undefined;
  isLoading: boolean;
}

const LEVEL_COLORS = {
  A: { bg: 'bg-green-100', text: 'text-green-700', bar: 'bg-green-500' },
  B: { bg: 'bg-blue-100', text: 'text-blue-700', bar: 'bg-blue-500' },
  C: { bg: 'bg-orange-100', text: 'text-orange-700', bar: 'bg-orange-500' },
};

function MasteryBadge({ level }: { level: 'A' | 'B' | 'C' }) {
  const colors = LEVEL_COLORS[level];
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-xs font-bold ${colors.bg} ${colors.text}`}
    >
      {level}
    </span>
  );
}

function ChapterMasteryItem({ chapter }: { chapter: ChapterMasteryDetail }) {
  const colors = LEVEL_COLORS[chapter.mastery_level];

  return (
    <div className="flex items-center gap-3 py-3">
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-foreground truncate">
          {chapter.chapter_title || `Глава ${chapter.chapter_order || chapter.chapter_id}`}
        </p>
        <div className="mt-1.5 flex items-center gap-2">
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
            <div
              className={`h-full rounded-full transition-all duration-500 ${colors.bar}`}
              style={{ width: `${Math.min(100, chapter.mastery_score)}%` }}
            />
          </div>
          <span className="w-10 text-right text-xs font-medium text-muted-foreground">
            {Math.round(chapter.mastery_score)}%
          </span>
        </div>
      </div>
      <MasteryBadge level={chapter.mastery_level} />
    </div>
  );
}

export function MasteryOverviewComponent({ data, isLoading }: MasteryOverviewProps) {
  const t = useTranslations('profile');

  if (isLoading) {
    return (
      <div className="space-y-3">
        {/* Summary skeleton */}
        <div className="animate-pulse rounded-xl bg-muted/50 p-3">
          <div className="flex items-center justify-between">
            <div className="h-4 w-24 rounded bg-muted" />
            <div className="flex gap-3">
              <div className="h-4 w-12 rounded bg-muted" />
              <div className="h-4 w-12 rounded bg-muted" />
              <div className="h-4 w-12 rounded bg-muted" />
            </div>
          </div>
        </div>
        {/* Items skeleton */}
        {[1, 2, 3].map((i) => (
          <div key={i} className="animate-pulse flex items-center gap-3 py-3">
            <div className="flex-1">
              <div className="h-4 w-32 rounded bg-muted" />
              <div className="mt-2 h-2 w-full rounded bg-muted" />
            </div>
            <div className="h-5 w-8 rounded-full bg-muted" />
          </div>
        ))}
      </div>
    );
  }

  if (!data || data.chapters.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-muted">
          <AlertCircle className="h-6 w-6 text-muted-foreground/50" />
        </div>
        <p className="text-sm text-muted-foreground">{t('mastery.noData')}</p>
      </div>
    );
  }

  // Sort chapters by order
  const sortedChapters = [...data.chapters].sort(
    (a, b) => (a.chapter_order ?? 0) - (b.chapter_order ?? 0)
  );

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="flex items-center justify-between rounded-xl bg-muted/50 p-3">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium">{t('mastery.overall')}</span>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <span className="font-medium text-green-600">A: {data.level_a_count}</span>
          <span className="font-medium text-blue-600">B: {data.level_b_count}</span>
          <span className="font-medium text-orange-600">C: {data.level_c_count}</span>
        </div>
      </div>

      {/* Chapter list */}
      <div className="divide-y divide-border">
        {sortedChapters.map((chapter) => (
          <ChapterMasteryItem key={chapter.id} chapter={chapter} />
        ))}
      </div>
    </div>
  );
}
