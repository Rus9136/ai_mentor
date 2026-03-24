'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import {
  useClasses,
  useAnalyticsSummary,
  useStrugglingTopics,
  useMasteryTrends,
  useSelfAssessmentSummary,
  useMetacognitiveAlerts,
} from '@/lib/hooks/use-teacher-data';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Loader2, MessageSquare } from 'lucide-react';

import { AnalyticsSummary, type AnalyticsTab } from './_components/analytics-summary';
import { StrugglingTopicsTab } from './_components/struggling-topics-tab';
import { MasteryTrendsTab } from './_components/mastery-trends-tab';
import { FeedbackTab } from './_components/feedback-tab';

export default function AnalyticsPage() {
  const t = useTranslations('analytics');
  const [period, setPeriod] = useState<'weekly' | 'monthly'>('weekly');
  const [selectedClassId, setSelectedClassId] = useState<number | undefined>(undefined);
  const [activeTab, setActiveTab] = useState<AnalyticsTab>('struggling');

  // Load teacher's classes for filter dropdown
  const { data: classes } = useClasses();

  // All analytics queries pass the selected class filter
  const { data: summary } = useAnalyticsSummary(selectedClassId);
  const { data: strugglingTopics, isLoading: topicsLoading } = useStrugglingTopics(selectedClassId);
  const { data: trends, isLoading: trendsLoading } = useMasteryTrends(period, selectedClassId);
  const { data: selfAssessment, isLoading: summaryLoading } = useSelfAssessmentSummary(selectedClassId);
  const { data: alerts, isLoading: alertsLoading } = useMetacognitiveAlerts(selectedClassId);

  const isLoading = topicsLoading || trendsLoading;

  if (isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with title and class filter */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-bold text-foreground">{t('title')}</h1>

        {classes && classes.length > 1 && (
          <Select
            value={selectedClassId ? String(selectedClassId) : 'all'}
            onValueChange={(v) => setSelectedClassId(v === 'all' ? undefined : Number(v))}
          >
            <SelectTrigger className="w-[220px]">
              <SelectValue placeholder={t('allClasses')} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t('allClasses')}</SelectItem>
              {classes.map((cls) => (
                <SelectItem key={cls.id} value={String(cls.id)}>
                  {cls.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      {/* Summary cards — clickable to navigate to tabs */}
      <AnalyticsSummary data={summary} onNavigate={setActiveTab} />

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as AnalyticsTab)} className="space-y-6">
        <TabsList>
          <TabsTrigger value="struggling">{t('strugglingTopics')}</TabsTrigger>
          <TabsTrigger value="trends">{t('masteryTrends')}</TabsTrigger>
          <TabsTrigger value="feedback" className="flex items-center gap-1.5">
            <MessageSquare className="h-3.5 w-3.5" />
            {t('feedback')}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="struggling">
          <StrugglingTopicsTab data={strugglingTopics} />
        </TabsContent>

        <TabsContent value="trends">
          <MasteryTrendsTab data={trends} period={period} onPeriodChange={setPeriod} />
        </TabsContent>

        <TabsContent value="feedback">
          <FeedbackTab
            summary={selfAssessment}
            alerts={alerts}
            isLoading={summaryLoading || alertsLoading}
            classId={selectedClassId}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
