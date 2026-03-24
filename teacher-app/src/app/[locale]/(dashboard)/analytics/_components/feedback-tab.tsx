'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { MessageSquare, XCircle, HelpCircle, ThumbsUp, Loader2, ChevronDown, ChevronRight } from 'lucide-react';
import { getParagraphAssessments } from '@/lib/api/teachers';
import type {
  SelfAssessmentSummaryResponse,
  MetacognitiveAlertsResponse,
  SelfAssessmentParagraphSummary,
} from '@/lib/api/teachers';

interface FeedbackTabProps {
  summary?: SelfAssessmentSummaryResponse;
  alerts?: MetacognitiveAlertsResponse;
  isLoading: boolean;
  classId?: number;
}

const ratingColors: Record<string, { bg: string; text: string; dot: string }> = {
  understood: { bg: 'bg-emerald-50', text: 'text-emerald-700', dot: 'bg-emerald-500' },
  questions: { bg: 'bg-amber-50', text: 'text-amber-700', dot: 'bg-amber-400' },
  difficult: { bg: 'bg-red-50', text: 'text-red-700', dot: 'bg-red-500' },
};

function ParagraphItem({
  p,
  classId,
}: {
  p: SelfAssessmentParagraphSummary;
  classId?: number;
}) {
  const t = useTranslations('analytics');
  const [expanded, setExpanded] = useState(false);

  const { data: detail, isLoading: detailLoading } = useQuery({
    queryKey: ['teacher', 'analytics', 'paragraph-assessments', p.paragraph_id, classId],
    queryFn: () => getParagraphAssessments(p.paragraph_id, classId),
    enabled: expanded,
  });

  const ratingLabel = (rating: string) => {
    switch (rating) {
      case 'understood':
        return t('understood');
      case 'questions':
        return t('hasQuestions');
      case 'difficult':
        return t('difficult');
      default:
        return rating;
    }
  };

  return (
    <div className="rounded-lg border transition-shadow hover:shadow-sm">
      {/* Clickable header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-start justify-between p-4 text-left"
      >
        <div className="flex items-start gap-2">
          {expanded ? (
            <ChevronDown className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
          ) : (
            <ChevronRight className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
          )}
          <div>
            <p className="font-medium">{p.paragraph_title}</p>
            <p className="text-sm text-muted-foreground">{p.chapter_title}</p>
          </div>
        </div>
        <span className="ml-2 shrink-0 text-sm text-muted-foreground">
          {p.total_assessments} {t('totalAssessments').toLowerCase()}
        </span>
      </button>

      {/* Stacked bar + legend (always visible) */}
      <div className="px-4 pb-3">
        <div className="flex h-3 overflow-hidden rounded-full">
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

      {/* Expanded: student list */}
      {expanded && (
        <div className="border-t px-4 py-3">
          {detailLoading ? (
            <div className="flex justify-center py-4">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : detail?.students && detail.students.length > 0 ? (
            <div className="space-y-1.5">
              {detail.students.map((s) => {
                const colors = ratingColors[s.rating] || ratingColors.understood;
                return (
                  <div
                    key={s.student_id}
                    className="flex items-center justify-between rounded-md px-3 py-2 text-sm hover:bg-muted/50"
                  >
                    <div className="flex items-center gap-2">
                      <span className={`inline-block h-2 w-2 rounded-full ${colors.dot}`} />
                      <span className="font-medium">
                        {s.last_name} {s.first_name}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${colors.bg} ${colors.text}`}
                      >
                        {ratingLabel(s.rating)}
                      </span>
                      {s.practice_score !== null && (
                        <span className="text-xs text-muted-foreground">
                          {t('practiceScore')}: {Math.round(s.practice_score)}%
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="py-2 text-center text-sm text-muted-foreground">—</p>
          )}
        </div>
      )}
    </div>
  );
}

export function FeedbackTab({ summary, alerts, isLoading, classId }: FeedbackTabProps) {
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
                <ParagraphItem key={p.paragraph_id} p={p} classId={classId} />
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
