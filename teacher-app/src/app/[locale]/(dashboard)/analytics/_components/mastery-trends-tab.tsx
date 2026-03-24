'use client';

import { useTranslations } from 'next-intl';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { MasteryTrendsResponse } from '@/lib/api/teachers';

interface MasteryTrendsTabProps {
  data?: MasteryTrendsResponse;
  period: 'weekly' | 'monthly';
  onPeriodChange: (period: 'weekly' | 'monthly') => void;
}

export function MasteryTrendsTab({ data, period, onPeriodChange }: MasteryTrendsTabProps) {
  const t = useTranslations('analytics');

  const getTrendIcon = (trend: string, size = 'h-4 w-4') => {
    switch (trend) {
      case 'improving':
        return <TrendingUp className={`${size} text-success`} />;
      case 'declining':
        return <TrendingDown className={`${size} text-destructive`} />;
      default:
        return <Minus className={`${size} text-muted-foreground`} />;
    }
  };

  const getTrendLabel = (trend: string) => {
    switch (trend) {
      case 'improving':
        return t('improving');
      case 'declining':
        return t('declining');
      default:
        return t('stable');
    }
  };

  return (
    <div className="space-y-6">
      {/* Period selector */}
      <div className="flex gap-2">
        <button
          onClick={() => onPeriodChange('weekly')}
          className={cn(
            'rounded-lg px-4 py-2 text-sm font-medium transition-colors',
            period === 'weekly'
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted text-muted-foreground hover:bg-muted/80'
          )}
        >
          {t('weekly')}
        </button>
        <button
          onClick={() => onPeriodChange('monthly')}
          className={cn(
            'rounded-lg px-4 py-2 text-sm font-medium transition-colors',
            period === 'monthly'
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted text-muted-foreground hover:bg-muted/80'
          )}
        >
          {t('monthly')}
        </button>
      </div>

      {/* Overall trend */}
      {data && (
        <Card>
          <CardHeader>
            <CardTitle>{t('overallTrend')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <div
                className={cn(
                  'flex h-16 w-16 items-center justify-center rounded-full',
                  data.overall_trend === 'improving'
                    ? 'bg-success/10'
                    : data.overall_trend === 'declining'
                    ? 'bg-destructive/10'
                    : 'bg-muted'
                )}
              >
                {getTrendIcon(data.overall_trend, 'h-8 w-8')}
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {getTrendLabel(data.overall_trend)}
                </p>
                <p
                  className={cn(
                    'text-lg font-semibold',
                    data.overall_change_percentage > 0
                      ? 'text-success'
                      : data.overall_change_percentage < 0
                      ? 'text-destructive'
                      : 'text-muted-foreground'
                  )}
                >
                  {data.overall_change_percentage > 0 ? '+' : ''}
                  {data.overall_change_percentage.toFixed(1)}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Class trends */}
      {data?.class_trends && data.class_trends.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>{t('classTrends')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {data.class_trends.map((classTrend) => (
                <div
                  key={classTrend.class_id}
                  className="flex items-center justify-between rounded-lg border p-4"
                >
                  <div className="flex items-center gap-3">
                    {getTrendIcon(classTrend.trend)}
                    <div>
                      <p className="font-medium">{classTrend.class_name}</p>
                      <p className="text-sm text-muted-foreground">
                        {Math.round(classTrend.previous_average)}% →{' '}
                        {Math.round(classTrend.current_average)}%
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p
                      className={cn(
                        'text-lg font-bold',
                        classTrend.change_percentage > 0
                          ? 'text-success'
                          : classTrend.change_percentage < 0
                          ? 'text-destructive'
                          : 'text-muted-foreground'
                      )}
                    >
                      {classTrend.change_percentage > 0 ? '+' : ''}
                      {classTrend.change_percentage.toFixed(1)}%
                    </p>
                    <div className="mt-1 flex items-center gap-2 text-xs">
                      {classTrend.promoted_to_a > 0 && (
                        <span className="text-success">
                          ↑A: {classTrend.promoted_to_a}
                        </span>
                      )}
                      {classTrend.demoted_to_c > 0 && (
                        <span className="text-destructive">
                          ↓C: {classTrend.demoted_to_c}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
