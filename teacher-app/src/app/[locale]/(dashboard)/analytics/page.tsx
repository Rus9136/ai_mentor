'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import {
  useStrugglingTopics,
  useMasteryTrends,
  useSelfAssessmentSummary,
  useMetacognitiveAlerts,
} from '@/lib/hooks/use-teacher-data';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  Loader2,
  BarChart3,
  MessageSquare,
  ThumbsUp,
  HelpCircle,
  XCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatRelativeDate } from '@/lib/utils';

export default function AnalyticsPage() {
  const t = useTranslations('analytics');
  const [period, setPeriod] = useState<'weekly' | 'monthly'>('weekly');

  const { data: strugglingTopics, isLoading: topicsLoading } = useStrugglingTopics();
  const { data: trends, isLoading: trendsLoading } = useMasteryTrends(period);
  const { data: summary, isLoading: summaryLoading } = useSelfAssessmentSummary();
  const { data: alerts, isLoading: alertsLoading } = useMetacognitiveAlerts();

  const isLoading = topicsLoading || trendsLoading;

  if (isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving':
        return <TrendingUp className="h-4 w-4 text-success" />;
      case 'declining':
        return <TrendingDown className="h-4 w-4 text-destructive" />;
      default:
        return <Minus className="h-4 w-4 text-muted-foreground" />;
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
      <div>
        <h1 className="text-2xl font-bold text-foreground">{t('title')}</h1>
      </div>

      <Tabs defaultValue="struggling" className="space-y-6">
        <TabsList>
          <TabsTrigger value="struggling">{t('strugglingTopics')}</TabsTrigger>
          <TabsTrigger value="trends">{t('masteryTrends')}</TabsTrigger>
          <TabsTrigger value="feedback" className="flex items-center gap-1.5">
            <MessageSquare className="h-3.5 w-3.5" />
            {t('feedback')}
          </TabsTrigger>
        </TabsList>

        {/* Struggling Topics */}
        <TabsContent value="struggling">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-warning" />
                {t('strugglingTopics')}
              </CardTitle>
              <CardDescription>{t('strugglingDescription')}</CardDescription>
            </CardHeader>
            <CardContent>
              {strugglingTopics && strugglingTopics.length > 0 ? (
                <div className="space-y-4">
                  {strugglingTopics.map((topic) => (
                    <div
                      key={topic.paragraph_id}
                      className="rounded-lg border border-destructive/30 bg-destructive/5 p-4"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="font-medium text-foreground">
                            {topic.paragraph_title}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {topic.chapter_title}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-lg font-bold text-destructive">
                            {topic.struggling_count}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {t('studentsStruggling')}
                          </p>
                        </div>
                      </div>

                      <div className="mt-3 flex items-center gap-4">
                        <div className="flex-1">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">
                              {Math.round(topic.struggling_percentage)}% учеников в C
                            </span>
                            <span className="text-muted-foreground">
                              Ср. балл: {Math.round(topic.average_score)}%
                            </span>
                          </div>
                          <Progress
                            value={topic.struggling_percentage}
                            className="mt-2 h-2"
                            indicatorClassName="bg-destructive"
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-12 text-center">
                  <BarChart3 className="mx-auto mb-4 h-12 w-12 text-muted-foreground/50" />
                  <p className="text-muted-foreground">
                    Нет сложных тем. Все ученики справляются хорошо!
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Mastery Trends */}
        <TabsContent value="trends">
          <div className="space-y-6">
            {/* Period selector */}
            <div className="flex gap-2">
              <button
                onClick={() => setPeriod('weekly')}
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
                onClick={() => setPeriod('monthly')}
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
            {trends && (
              <Card>
                <CardHeader>
                  <CardTitle>Общий тренд</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-4">
                    <div
                      className={cn(
                        'flex h-16 w-16 items-center justify-center rounded-full',
                        trends.overall_trend === 'improving'
                          ? 'bg-success/10'
                          : trends.overall_trend === 'declining'
                          ? 'bg-destructive/10'
                          : 'bg-muted'
                      )}
                    >
                      {trends.overall_trend === 'improving' && (
                        <TrendingUp className="h-8 w-8 text-success" />
                      )}
                      {trends.overall_trend === 'declining' && (
                        <TrendingDown className="h-8 w-8 text-destructive" />
                      )}
                      {trends.overall_trend === 'stable' && (
                        <Minus className="h-8 w-8 text-muted-foreground" />
                      )}
                    </div>
                    <div>
                      <p className="text-2xl font-bold">
                        {getTrendLabel(trends.overall_trend)}
                      </p>
                      <p
                        className={cn(
                          'text-lg font-semibold',
                          trends.overall_change_percentage > 0
                            ? 'text-success'
                            : trends.overall_change_percentage < 0
                            ? 'text-destructive'
                            : 'text-muted-foreground'
                        )}
                      >
                        {trends.overall_change_percentage > 0 ? '+' : ''}
                        {trends.overall_change_percentage.toFixed(1)}%
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Class trends */}
            {trends?.class_trends && trends.class_trends.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Тренды по классам</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {trends.class_trends.map((classTrend) => (
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
        </TabsContent>

        {/* Self-Assessment Feedback */}
        <TabsContent value="feedback">
          {summaryLoading || alertsLoading ? (
            <div className="flex min-h-[200px] items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
            </div>
          ) : (
            <div className="space-y-6">
              {/* Paragraph breakdown */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MessageSquare className="h-5 w-5 text-primary" />
                    {t('feedback')}
                  </CardTitle>
                  <CardDescription>{t('feedbackDescription')}</CardDescription>
                </CardHeader>
                <CardContent>
                  {summary && summary.paragraphs.length > 0 ? (
                    <div className="space-y-3">
                      {summary.paragraphs.map((p) => (
                        <div
                          key={p.paragraph_id}
                          className="rounded-lg border p-4"
                        >
                          <div className="flex items-start justify-between">
                            <div>
                              <p className="font-medium">{p.paragraph_title}</p>
                              <p className="text-sm text-muted-foreground">
                                {p.chapter_title}
                              </p>
                            </div>
                            <span className="text-sm text-muted-foreground">
                              {p.total_assessments} {t('totalAssessments').toLowerCase()}
                            </span>
                          </div>

                          {/* Stacked bar */}
                          <div className="mt-3 flex h-3 overflow-hidden rounded-full">
                            {p.understood_pct > 0 && (
                              <div
                                className="bg-emerald-500 transition-all"
                                style={{ width: `${p.understood_pct}%` }}
                                title={`${t('understood')}: ${p.understood_pct}%`}
                              />
                            )}
                            {p.questions_pct > 0 && (
                              <div
                                className="bg-amber-400 transition-all"
                                style={{ width: `${p.questions_pct}%` }}
                                title={`${t('hasQuestions')}: ${p.questions_pct}%`}
                              />
                            )}
                            {p.difficult_pct > 0 && (
                              <div
                                className="bg-red-500 transition-all"
                                style={{ width: `${p.difficult_pct}%` }}
                                title={`${t('difficult')}: ${p.difficult_pct}%`}
                              />
                            )}
                          </div>

                          {/* Legend */}
                          <div className="mt-2 flex flex-wrap gap-4 text-xs text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <span className="inline-block h-2 w-2 rounded-full bg-emerald-500" />
                              {t('understood')} {p.understood_pct}%
                            </span>
                            <span className="flex items-center gap-1">
                              <span className="inline-block h-2 w-2 rounded-full bg-amber-400" />
                              {t('hasQuestions')} {p.questions_pct}%
                            </span>
                            <span className="flex items-center gap-1">
                              <span className="inline-block h-2 w-2 rounded-full bg-red-500" />
                              {t('difficult')} {p.difficult_pct}%
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="py-12 text-center">
                      <MessageSquare className="mx-auto mb-4 h-12 w-12 text-muted-foreground/50" />
                      <p className="text-muted-foreground">{t('noAssessments')}</p>
                      <p className="mt-1 text-sm text-muted-foreground/70">
                        {t('noAssessmentsHint')}
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Metacognitive alerts */}
              {alerts && (alerts.overconfident.length > 0 || alerts.underconfident.length > 0) ? (
                <div className="grid gap-6 lg:grid-cols-2">
                  {/* Overconfident */}
                  <Card className="border-red-200">
                    <CardHeader className="pb-3">
                      <CardTitle className="flex items-center gap-2 text-base">
                        <XCircle className="h-4 w-4 text-destructive" />
                        {t('overconfident')}
                      </CardTitle>
                      <CardDescription className="text-xs">
                        {t('overconfidentDesc')}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      {alerts.overconfident.length > 0 ? (
                        <div className="space-y-2">
                          {alerts.overconfident.map((a, i) => (
                            <div
                              key={`over-${i}`}
                              className="flex items-center justify-between rounded-lg border border-red-100 bg-red-50/50 p-3 text-sm"
                            >
                              <div>
                                <p className="font-medium">
                                  {a.last_name} {a.first_name}
                                </p>
                                <p className="text-xs text-muted-foreground">
                                  {a.paragraph_title}
                                </p>
                              </div>
                              <div className="text-right">
                                <p className="text-xs text-muted-foreground">
                                  {t('practiceScore')}
                                </p>
                                <p className="font-bold text-destructive">
                                  {Math.round(a.practice_score)}%
                                </p>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="py-4 text-center text-sm text-muted-foreground">
                          {t('noAlerts')}
                        </p>
                      )}
                    </CardContent>
                  </Card>

                  {/* Underconfident */}
                  <Card className="border-blue-200">
                    <CardHeader className="pb-3">
                      <CardTitle className="flex items-center gap-2 text-base">
                        <HelpCircle className="h-4 w-4 text-blue-500" />
                        {t('underconfident')}
                      </CardTitle>
                      <CardDescription className="text-xs">
                        {t('underconfidentDesc')}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      {alerts.underconfident.length > 0 ? (
                        <div className="space-y-2">
                          {alerts.underconfident.map((a, i) => (
                            <div
                              key={`under-${i}`}
                              className="flex items-center justify-between rounded-lg border border-blue-100 bg-blue-50/50 p-3 text-sm"
                            >
                              <div>
                                <p className="font-medium">
                                  {a.last_name} {a.first_name}
                                </p>
                                <p className="text-xs text-muted-foreground">
                                  {a.paragraph_title}
                                </p>
                              </div>
                              <div className="text-right">
                                <p className="text-xs text-muted-foreground">
                                  {t('practiceScore')}
                                </p>
                                <p className="font-bold text-blue-600">
                                  {Math.round(a.practice_score)}%
                                </p>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="py-4 text-center text-sm text-muted-foreground">
                          {t('noAlerts')}
                        </p>
                      )}
                    </CardContent>
                  </Card>
                </div>
              ) : alerts ? (
                <Card>
                  <CardContent className="py-8 text-center">
                    <ThumbsUp className="mx-auto mb-3 h-10 w-10 text-success/50" />
                    <p className="text-muted-foreground">{t('noAlerts')}</p>
                    <p className="mt-1 text-sm text-muted-foreground/70">
                      {t('noAlertsHint')}
                    </p>
                  </CardContent>
                </Card>
              ) : null}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
