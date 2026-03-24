'use client';

import { useTranslations } from 'next-intl';
import { Card, CardContent } from '@/components/ui/card';
import { Users, Target, AlertTriangle, Bell, Activity } from 'lucide-react';
import type { AnalyticsSummaryResponse } from '@/lib/api/teachers';

interface AnalyticsSummaryProps {
  data?: AnalyticsSummaryResponse;
}

export function AnalyticsSummary({ data }: AnalyticsSummaryProps) {
  const t = useTranslations('analytics');

  const metrics = [
    {
      label: t('summaryStudents'),
      value: data?.total_students ?? 0,
      icon: Users,
      color: 'text-blue-600',
      bg: 'bg-blue-50',
    },
    {
      label: t('summaryMastery'),
      value: `${data?.average_mastery?.toFixed(1) ?? 0}%`,
      icon: Target,
      color: 'text-emerald-600',
      bg: 'bg-emerald-50',
    },
    {
      label: t('summaryStruggling'),
      value: data?.struggling_topics_count ?? 0,
      icon: AlertTriangle,
      color: 'text-amber-600',
      bg: 'bg-amber-50',
    },
    {
      label: t('summaryAlerts'),
      value: data?.metacognitive_alerts_count ?? 0,
      icon: Bell,
      color: 'text-red-600',
      bg: 'bg-red-50',
    },
    {
      label: t('summaryActive'),
      value: data?.active_students_count ?? 0,
      icon: Activity,
      color: 'text-violet-600',
      bg: 'bg-violet-50',
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {metrics.map((m) => (
        <Card key={m.label} className="border-0 shadow-sm">
          <CardContent className="flex items-center gap-3 p-4">
            <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${m.bg}`}>
              <m.icon className={`h-5 w-5 ${m.color}`} />
            </div>
            <div className="min-w-0">
              <p className="text-2xl font-bold leading-none">{m.value}</p>
              <p className="mt-1 truncate text-xs text-muted-foreground">{m.label}</p>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
