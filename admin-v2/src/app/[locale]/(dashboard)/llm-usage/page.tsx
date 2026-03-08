'use client';

import { useState, useMemo } from 'react';
import { format, subDays } from 'date-fns';
import { Activity, AlertTriangle, Clock, Zap, Hash, ArrowUpDown } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { RoleGuard } from '@/components/auth';
import {
  useLLMUsageStats,
  useLLMUsageDaily,
} from '@/lib/hooks/use-llm-usage';
import type { LLMUsageDailyStats } from '@/lib/api/llm-usage';

type Period = '7d' | '14d' | '30d';

const FEATURE_LABELS: Record<string, string> = {
  chat: 'Чат',
  rag: 'RAG / Объяснения',
  lesson_plan: 'Планы уроков',
  homework_generation: 'Генерация ДЗ',
  homework_grading: 'Проверка ДЗ',
  audio_text: 'Аудио текст',
  system: 'Системные',
};

function formatNumber(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
  return n.toString();
}

export default function LLMUsagePage() {
  const [period, setPeriod] = useState<Period>('30d');

  const dateRange = useMemo(() => {
    const days = period === '7d' ? 7 : period === '14d' ? 14 : 30;
    return {
      date_from: format(subDays(new Date(), days), 'yyyy-MM-dd'),
      date_to: format(new Date(), 'yyyy-MM-dd'),
    };
  }, [period]);

  const { data: stats, isLoading: statsLoading } = useLLMUsageStats(dateRange);
  const { data: daily, isLoading: dailyLoading } = useLLMUsageDaily(dateRange);

  return (
    <RoleGuard allowedRoles={['super_admin']}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">LLM Мониторинг</h1>
            <p className="text-muted-foreground">
              Использование токенов по всем AI-сервисам
            </p>
          </div>
          <div className="flex gap-1">
            {(['7d', '14d', '30d'] as Period[]).map((p) => (
              <Button
                key={p}
                variant={period === p ? 'default' : 'outline'}
                size="sm"
                onClick={() => setPeriod(p)}
              >
                {p === '7d' ? '7 дней' : p === '14d' ? '14 дней' : '30 дней'}
              </Button>
            ))}
          </div>
        </div>

        {/* Summary Cards */}
        {statsLoading ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Card key={i}>
                <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                  <Skeleton className="h-4 w-24" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-8 w-20" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : stats ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                <CardTitle className="text-sm font-medium">Всего вызовов</CardTitle>
                <Hash className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatNumber(stats.total_calls)}</div>
                <p className="text-xs text-muted-foreground">
                  {stats.failed_calls > 0 && (
                    <span className="text-destructive">
                      {stats.failed_calls} ошибок
                    </span>
                  )}
                  {stats.failed_calls === 0 && 'Все успешные'}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                <CardTitle className="text-sm font-medium">Токены (всего)</CardTitle>
                <Zap className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatNumber(stats.total_tokens)}</div>
                <p className="text-xs text-muted-foreground">
                  Prompt: {formatNumber(stats.total_prompt_tokens)} / Completion: {formatNumber(stats.total_completion_tokens)}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                <CardTitle className="text-sm font-medium">Средняя задержка</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats.avg_latency_ms ? `${(stats.avg_latency_ms / 1000).toFixed(1)}s` : '—'}
                </div>
                <p className="text-xs text-muted-foreground">Время ответа LLM</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                <CardTitle className="text-sm font-medium">Ср. токенов / вызов</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats.total_calls > 0
                    ? formatNumber(Math.round(stats.total_tokens / stats.total_calls))
                    : '—'}
                </div>
                <p className="text-xs text-muted-foreground">Среднее потребление</p>
              </CardContent>
            </Card>
          </div>
        ) : null}

        {/* Daily Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Токены по дням</CardTitle>
          </CardHeader>
          <CardContent>
            {dailyLoading ? (
              <Skeleton className="h-64 w-full" />
            ) : daily && daily.length > 0 ? (
              <DailyChart data={daily} />
            ) : (
              <div className="flex items-center justify-center h-64 text-muted-foreground">
                Нет данных за выбранный период
              </div>
            )}
          </CardContent>
        </Card>

        {/* Feature Breakdown */}
        {stats && stats.by_feature.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>По фичам</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {stats.by_feature
                  .sort((a, b) => b.total_tokens - a.total_tokens)
                  .map((feat) => {
                    const pct = stats.total_tokens > 0
                      ? (feat.total_tokens / stats.total_tokens) * 100
                      : 0;
                    return (
                      <div key={feat.feature} className="space-y-1">
                        <div className="flex items-center justify-between text-sm">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">
                              {FEATURE_LABELS[feat.feature] || feat.feature}
                            </span>
                            {feat.error_count > 0 && (
                              <Badge variant="destructive" className="text-xs">
                                <AlertTriangle className="h-3 w-3 mr-1" />
                                {feat.error_count}
                              </Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-3 text-muted-foreground">
                            <span>{formatNumber(feat.total_tokens)} токенов</span>
                            <span>{feat.total_calls} выз.</span>
                            {feat.avg_latency_ms && (
                              <span>{(feat.avg_latency_ms / 1000).toFixed(1)}s</span>
                            )}
                          </div>
                        </div>
                        <div className="h-2 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary rounded-full transition-all"
                            style={{ width: `${Math.max(pct, 0.5)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Model Breakdown */}
        {stats && stats.by_model.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>По моделям</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2 font-medium">Модель</th>
                      <th className="text-left py-2 font-medium">Провайдер</th>
                      <th className="text-right py-2 font-medium">Вызовы</th>
                      <th className="text-right py-2 font-medium">Токены</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.by_model
                      .sort((a, b) => b.total_tokens - a.total_tokens)
                      .map((m) => (
                        <tr key={`${m.provider}-${m.model}`} className="border-b last:border-0">
                          <td className="py-2 font-mono text-xs">{m.model}</td>
                          <td className="py-2">
                            <Badge variant="outline">{m.provider}</Badge>
                          </td>
                          <td className="py-2 text-right">{formatNumber(m.total_calls)}</td>
                          <td className="py-2 text-right font-medium">
                            {formatNumber(m.total_tokens)}
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </RoleGuard>
  );
}

function DailyChart({ data }: { data: LLMUsageDailyStats[] }) {
  const maxTokens = Math.max(...data.map((d) => d.total_tokens), 1);

  return (
    <div className="space-y-2">
      {/* Bar chart */}
      <div className="flex items-end gap-1 h-52">
        {data.map((day) => {
          const height = (day.total_tokens / maxTokens) * 100;
          const promptPct =
            day.total_tokens > 0 ? (day.prompt_tokens / day.total_tokens) * 100 : 50;
          return (
            <div
              key={day.date}
              className="flex-1 flex flex-col items-center group relative"
            >
              {/* Tooltip */}
              <div className="absolute bottom-full mb-2 hidden group-hover:block z-10">
                <div className="bg-popover text-popover-foreground shadow-md rounded-md px-3 py-2 text-xs whitespace-nowrap border">
                  <div className="font-medium">{format(new Date(day.date), 'dd.MM')}</div>
                  <div>{formatNumber(day.total_tokens)} токенов</div>
                  <div>{day.total_calls} вызовов</div>
                  {day.error_count > 0 && (
                    <div className="text-destructive">{day.error_count} ошибок</div>
                  )}
                </div>
              </div>
              {/* Bar */}
              <div
                className="w-full rounded-t-sm overflow-hidden transition-all relative"
                style={{ height: `${Math.max(height, 1)}%` }}
              >
                {/* Prompt portion */}
                <div
                  className="absolute bottom-0 w-full bg-primary/70"
                  style={{ height: `${promptPct}%` }}
                />
                {/* Completion portion */}
                <div
                  className="absolute top-0 w-full bg-primary"
                  style={{ height: `${100 - promptPct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
      {/* X-axis labels */}
      <div className="flex gap-1">
        {data.map((day, i) => {
          // Show label every ~5 days to avoid crowding
          const showLabel = data.length <= 14 || i % Math.ceil(data.length / 7) === 0 || i === data.length - 1;
          return (
            <div key={day.date} className="flex-1 text-center">
              {showLabel && (
                <span className="text-xs text-muted-foreground">
                  {format(new Date(day.date), 'dd.MM')}
                </span>
              )}
            </div>
          );
        })}
      </div>
      {/* Legend */}
      <div className="flex items-center justify-center gap-4 text-xs text-muted-foreground pt-2">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-sm bg-primary" />
          <span>Completion</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-sm bg-primary/70" />
          <span>Prompt</span>
        </div>
      </div>
    </div>
  );
}
