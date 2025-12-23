'use client';

import { useTranslations } from 'next-intl';
import { cn } from '@/lib/utils';
import type { MasteryDistribution } from '@/lib/api/teachers';

interface MasteryDistributionChartProps {
  distribution: MasteryDistribution;
  className?: string;
}

export function MasteryDistributionChart({
  distribution,
  className,
}: MasteryDistributionChartProps) {
  const t = useTranslations('dashboard');

  const total =
    distribution.level_a +
    distribution.level_b +
    distribution.level_c +
    distribution.not_started;

  const getPercent = (value: number) =>
    total > 0 ? Math.round((value / total) * 100) : 0;

  const levels = [
    {
      key: 'A',
      label: t('levelA'),
      value: distribution.level_a,
      percent: getPercent(distribution.level_a),
      color: 'bg-success',
      textColor: 'text-success',
    },
    {
      key: 'B',
      label: t('levelB'),
      value: distribution.level_b,
      percent: getPercent(distribution.level_b),
      color: 'bg-warning',
      textColor: 'text-warning',
    },
    {
      key: 'C',
      label: t('levelC'),
      value: distribution.level_c,
      percent: getPercent(distribution.level_c),
      color: 'bg-destructive',
      textColor: 'text-destructive',
    },
    {
      key: 'N',
      label: t('notStarted'),
      value: distribution.not_started,
      percent: getPercent(distribution.not_started),
      color: 'bg-muted',
      textColor: 'text-muted-foreground',
    },
  ];

  return (
    <div className={cn('space-y-4', className)}>
      {/* Stacked bar */}
      <div className="flex h-4 overflow-hidden rounded-full bg-muted">
        {levels.map(
          (level) =>
            level.percent > 0 && (
              <div
                key={level.key}
                className={cn('transition-all', level.color)}
                style={{ width: `${level.percent}%` }}
              />
            )
        )}
      </div>

      {/* Legend */}
      <div className="grid grid-cols-2 gap-3">
        {levels.map((level) => (
          <div key={level.key} className="flex items-center gap-2">
            <div className={cn('h-3 w-3 rounded-full', level.color)} />
            <div className="flex-1 min-w-0">
              <p className="text-xs text-muted-foreground truncate">
                {level.label}
              </p>
            </div>
            <p className={cn('text-sm font-semibold', level.textColor)}>
              {level.value}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
