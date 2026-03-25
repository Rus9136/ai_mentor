'use client';

import { useTranslations } from 'next-intl';
import { Card, CardContent } from '@/components/ui/card';
import { Users, Target, AlertTriangle, Bell, Activity, ClipboardCheck } from 'lucide-react';
import type { AnalyticsSummaryResponse, DiagnosticResultsResponse } from '@/lib/api/teachers';

export type AnalyticsTab = 'diagnostic' | 'struggling' | 'trends' | 'feedback';

interface AnalyticsSummaryProps {
  data?: AnalyticsSummaryResponse;
  diagnosticData?: DiagnosticResultsResponse;
  onNavigate?: (tab: AnalyticsTab) => void;
}

export function AnalyticsSummary({ data, diagnosticData, onNavigate }: AnalyticsSummaryProps) {
  const t = useTranslations('analytics');

  const diagnosticAvg = diagnosticData?.average_score;
  const diagnosticLabel = diagnosticAvg !== null && diagnosticAvg !== undefined
    ? `${Math.round(diagnosticAvg)}%`
    : '—';

  const metrics = [
    {
      label: t('diagnosticBaseline'),
      value: diagnosticLabel,
      icon: ClipboardCheck,
      color: 'text-indigo-600',
      bg: 'bg-indigo-50',
      tab: 'diagnostic' as AnalyticsTab,
    },
    {
      label: t('summaryStudents'),
      value: data?.total_students ?? 0,
      icon: Users,
      color: 'text-blue-600',
      bg: 'bg-blue-50',
      tab: undefined as AnalyticsTab | undefined,
    },
    {
      label: t('summaryMastery'),
      value: `${data?.average_mastery?.toFixed(1) ?? 0}%`,
      icon: Target,
      color: 'text-emerald-600',
      bg: 'bg-emerald-50',
      tab: 'trends' as AnalyticsTab,
    },
    {
      label: t('summaryStruggling'),
      value: data?.struggling_topics_count ?? 0,
      icon: AlertTriangle,
      color: 'text-amber-600',
      bg: 'bg-amber-50',
      tab: 'struggling' as AnalyticsTab,
    },
    {
      label: t('summaryAlerts'),
      value: data?.metacognitive_alerts_count ?? 0,
      icon: Bell,
      color: 'text-red-600',
      bg: 'bg-red-50',
      tab: 'feedback' as AnalyticsTab,
    },
    {
      label: t('summaryActive'),
      value: data?.active_students_count ?? 0,
      icon: Activity,
      color: 'text-violet-600',
      bg: 'bg-violet-50',
      tab: undefined as AnalyticsTab | undefined,
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      {metrics.map((m) => {
        const clickable = !!m.tab && !!onNavigate;
        return (
          <Card
            key={m.label}
            className={`border-0 shadow-sm transition-shadow ${clickable ? 'cursor-pointer hover:shadow-md' : ''}`}
            onClick={clickable ? () => onNavigate!(m.tab!) : undefined}
          >
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
        );
      })}
    </div>
  );
}
