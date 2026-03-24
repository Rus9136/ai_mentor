'use client';

import { useTranslations } from 'next-intl';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { MessageSquare, XCircle, HelpCircle, ThumbsUp, Loader2 } from 'lucide-react';
import type { SelfAssessmentSummaryResponse, MetacognitiveAlertsResponse } from '@/lib/api/teachers';

interface FeedbackTabProps {
  summary?: SelfAssessmentSummaryResponse;
  alerts?: MetacognitiveAlertsResponse;
  isLoading: boolean;
}

export function FeedbackTab({ summary, alerts, isLoading }: FeedbackTabProps) {
  const t = useTranslations('analytics');

  if (isLoading) {
    return (
      <div className="flex min-h-[200px] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    );
  }

  return (
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
                <div key={p.paragraph_id} className="rounded-lg border p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium">{p.paragraph_title}</p>
                      <p className="text-sm text-muted-foreground">{p.chapter_title}</p>
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
              <p className="mt-1 text-sm text-muted-foreground/70">{t('noAssessmentsHint')}</p>
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
              <CardDescription className="text-xs">{t('overconfidentDesc')}</CardDescription>
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
                        <p className="text-xs text-muted-foreground">{a.paragraph_title}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-muted-foreground">{t('practiceScore')}</p>
                        <p className="font-bold text-destructive">{Math.round(a.practice_score)}%</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="py-4 text-center text-sm text-muted-foreground">{t('noAlerts')}</p>
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
              <CardDescription className="text-xs">{t('underconfidentDesc')}</CardDescription>
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
                        <p className="text-xs text-muted-foreground">{a.paragraph_title}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-muted-foreground">{t('practiceScore')}</p>
                        <p className="font-bold text-blue-600">{Math.round(a.practice_score)}%</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="py-4 text-center text-sm text-muted-foreground">{t('noAlerts')}</p>
              )}
            </CardContent>
          </Card>
        </div>
      ) : alerts ? (
        <Card>
          <CardContent className="py-8 text-center">
            <ThumbsUp className="mx-auto mb-3 h-10 w-10 text-success/50" />
            <p className="text-muted-foreground">{t('noAlerts')}</p>
            <p className="mt-1 text-sm text-muted-foreground/70">{t('noAlertsHint')}</p>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
