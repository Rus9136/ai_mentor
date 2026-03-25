'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import {
  ClipboardCheck,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
} from 'lucide-react';
import { useDiagnosticAttemptAnswers } from '@/lib/hooks/use-teacher-data';
import type { DiagnosticResultsResponse, DiagnosticStudentResult } from '@/lib/api/teachers';
import { cn } from '@/lib/utils';

interface DiagnosticTabProps {
  data?: DiagnosticResultsResponse;
  isLoading?: boolean;
}

function ScoreBadge({ score }: { score: number | null }) {
  if (score === null) return <span className="text-muted-foreground">—</span>;

  const color =
    score >= 85
      ? 'bg-emerald-100 text-emerald-700'
      : score >= 60
        ? 'bg-amber-100 text-amber-700'
        : 'bg-red-100 text-red-700';

  return (
    <span className={cn('rounded-full px-2.5 py-0.5 text-xs font-semibold', color)}>
      {Math.round(score)}%
    </span>
  );
}

function formatTime(seconds: number | null): string {
  if (!seconds) return '—';
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m > 0 ? `${m} мин ${s} сек` : `${s} сек`;
}

function StudentRow({ result }: { result: DiagnosticStudentResult }) {
  const t = useTranslations('analytics');
  const [expanded, setExpanded] = useState(false);
  const { data: answers, isLoading } = useDiagnosticAttemptAnswers(
    expanded ? result.attempt_id : null
  );

  return (
    <div className="rounded-lg border">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between p-3 text-left hover:bg-muted/50 transition-colors"
      >
        <div className="flex items-center gap-3 min-w-0 flex-1">
          {expanded ? (
            <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
          )}
          <div className="min-w-0">
            <p className="text-sm font-medium truncate">
              {result.last_name} {result.first_name}
            </p>
            <p className="text-xs text-muted-foreground truncate">
              {result.subject_name || result.textbook_title || result.test_title}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 shrink-0">
          <div className="text-xs text-muted-foreground text-right hidden sm:block">
            <span>{result.questions_correct}/{result.questions_total}</span>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground hidden md:flex">
            <Clock className="h-3 w-3" />
            {formatTime(result.time_spent)}
          </div>
          <ScoreBadge score={result.score_percent} />
        </div>
      </button>

      {expanded && (
        <div className="border-t px-3 pb-3">
          {isLoading ? (
            <div className="flex items-center justify-center py-6">
              <Loader2 className="h-5 w-5 animate-spin text-primary" />
            </div>
          ) : answers ? (
            <div className="mt-3 space-y-2">
              {answers.answers.map((answer, idx) => (
                <div
                  key={answer.question_id}
                  className={cn(
                    'rounded-lg border p-3',
                    answer.is_correct
                      ? 'border-emerald-200 bg-emerald-50/50'
                      : 'border-red-200 bg-red-50/50'
                  )}
                >
                  <div className="flex items-start gap-2">
                    {answer.is_correct ? (
                      <CheckCircle2 className="h-4 w-4 mt-0.5 shrink-0 text-emerald-600" />
                    ) : (
                      <XCircle className="h-4 w-4 mt-0.5 shrink-0 text-red-600" />
                    )}
                    <div className="min-w-0 flex-1">
                      <p className="text-sm">
                        <span className="font-medium text-muted-foreground">{idx + 1}.</span>{' '}
                        {answer.question_text}
                      </p>

                      {answer.options.length > 0 && (
                        <div className="mt-2 space-y-1">
                          {answer.options.map((opt) => {
                            const isSelected = answer.selected_option_ids?.includes(opt.id);
                            const isCorrectOption = opt.is_correct;

                            return (
                              <div
                                key={opt.id}
                                className={cn(
                                  'flex items-center gap-2 rounded px-2 py-1 text-xs',
                                  isCorrectOption && 'bg-emerald-100/80 font-medium text-emerald-800',
                                  isSelected && !isCorrectOption && 'bg-red-100/80 text-red-800 line-through',
                                  !isSelected && !isCorrectOption && 'text-muted-foreground'
                                )}
                              >
                                {isCorrectOption && <CheckCircle2 className="h-3 w-3 text-emerald-600" />}
                                {isSelected && !isCorrectOption && <XCircle className="h-3 w-3 text-red-500" />}
                                {!isSelected && !isCorrectOption && <span className="w-3" />}
                                <span>{opt.text}</span>
                              </div>
                            );
                          })}
                        </div>
                      )}

                      {answer.answer_text && (
                        <p className="mt-1 text-xs text-muted-foreground">
                          {t('diagnosticAnswer')}: {answer.answer_text}
                        </p>
                      )}

                      {answer.explanation && (
                        <p className="mt-1.5 text-xs italic text-muted-foreground">
                          {answer.explanation}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="py-4 text-center text-sm text-muted-foreground">
              {t('diagnosticNoAnswers')}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export function DiagnosticTab({ data, isLoading }: DiagnosticTabProps) {
  const t = useTranslations('analytics');

  if (isLoading) {
    return (
      <div className="flex min-h-[200px] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    );
  }

  if (!data || data.results.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ClipboardCheck className="h-5 w-5 text-blue-500" />
            {t('diagnosticTitle')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="py-12 text-center">
            <ClipboardCheck className="mx-auto mb-4 h-12 w-12 text-muted-foreground/50" />
            <p className="text-muted-foreground">{t('diagnosticNoData')}</p>
            <p className="mt-1 text-sm text-muted-foreground/70">{t('diagnosticNoDataHint')}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const dist = data.distribution;
  const total = dist.range_0_40 + dist.range_40_60 + dist.range_60_85 + dist.range_85_100;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ClipboardCheck className="h-5 w-5 text-blue-500" />
          {t('diagnosticTitle')}
        </CardTitle>
        <CardDescription>{t('diagnosticDescription')}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Summary stats */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div className="rounded-lg border p-3 text-center">
            <p className="text-2xl font-bold text-foreground">{data.students_tested}</p>
            <p className="text-xs text-muted-foreground">{t('diagnosticTested')}</p>
          </div>
          <div className="rounded-lg border p-3 text-center">
            <p className="text-2xl font-bold text-foreground">
              {data.average_score !== null ? `${Math.round(data.average_score)}%` : '—'}
            </p>
            <p className="text-xs text-muted-foreground">{t('diagnosticAvgScore')}</p>
          </div>
          <div className="rounded-lg border p-3 text-center">
            <p className="text-2xl font-bold text-emerald-600">{dist.range_85_100}</p>
            <p className="text-xs text-muted-foreground">85-100%</p>
          </div>
          <div className="rounded-lg border p-3 text-center">
            <p className="text-2xl font-bold text-red-600">{dist.range_0_40}</p>
            <p className="text-xs text-muted-foreground">0-39%</p>
          </div>
        </div>

        {/* Distribution bar */}
        {total > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium text-muted-foreground">{t('diagnosticDistribution')}</p>
            <div className="flex h-4 w-full overflow-hidden rounded-full bg-muted">
              {dist.range_85_100 > 0 && (
                <div
                  className="bg-emerald-500 transition-all"
                  style={{ width: `${(dist.range_85_100 / total) * 100}%` }}
                  title={`85-100%: ${dist.range_85_100}`}
                />
              )}
              {dist.range_60_85 > 0 && (
                <div
                  className="bg-amber-400 transition-all"
                  style={{ width: `${(dist.range_60_85 / total) * 100}%` }}
                  title={`60-84%: ${dist.range_60_85}`}
                />
              )}
              {dist.range_40_60 > 0 && (
                <div
                  className="bg-orange-400 transition-all"
                  style={{ width: `${(dist.range_40_60 / total) * 100}%` }}
                  title={`40-59%: ${dist.range_40_60}`}
                />
              )}
              {dist.range_0_40 > 0 && (
                <div
                  className="bg-red-500 transition-all"
                  style={{ width: `${(dist.range_0_40 / total) * 100}%` }}
                  title={`0-39%: ${dist.range_0_40}`}
                />
              )}
            </div>
            <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <span className="inline-block h-2.5 w-2.5 rounded-full bg-emerald-500" />
                85-100% ({dist.range_85_100})
              </span>
              <span className="flex items-center gap-1">
                <span className="inline-block h-2.5 w-2.5 rounded-full bg-amber-400" />
                60-84% ({dist.range_60_85})
              </span>
              <span className="flex items-center gap-1">
                <span className="inline-block h-2.5 w-2.5 rounded-full bg-orange-400" />
                40-59% ({dist.range_40_60})
              </span>
              <span className="flex items-center gap-1">
                <span className="inline-block h-2.5 w-2.5 rounded-full bg-red-500" />
                0-39% ({dist.range_0_40})
              </span>
            </div>
          </div>
        )}

        {/* Student results list */}
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">{t('diagnosticStudentResults')}</p>
          {data.results.map((result) => (
            <StudentRow key={result.attempt_id} result={result} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
