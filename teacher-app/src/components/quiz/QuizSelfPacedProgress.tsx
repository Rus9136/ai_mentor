'use client';

import { useTranslations } from 'next-intl';
import { useStudentProgress } from '@/lib/hooks/use-quiz';
import { CheckCircle, Clock, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface QuizSelfPacedProgressProps {
  sessionId: number;
  totalQuestions: number;
  onEndQuiz: () => void;
}

interface ProgressItem {
  student_id: number;
  student_name: string;
  answered: number;
  total: number;
  correct: number;
  total_score: number;
}

export default function QuizSelfPacedProgress({ sessionId, totalQuestions, onEndQuiz }: QuizSelfPacedProgressProps) {
  const t = useTranslations('quiz');
  const { data: progress, isLoading } = useStudentProgress(sessionId);

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const students: ProgressItem[] = progress || [];
  const allFinished = students.length > 0 && students.every((s) => s.answered >= s.total);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold">{t('selfPacedProgress')}</h2>
          <p className="text-sm text-muted-foreground">
            {t('totalQuestions')}: {totalQuestions}
          </p>
        </div>
        <Button variant="destructive" size="sm" onClick={onEndQuiz}>
          {t('endQuiz')}
        </Button>
      </div>

      {allFinished && (
        <div className="rounded-lg bg-green-50 p-3 text-center text-sm font-medium text-green-700">
          {t('allStudentsFinished')}
        </div>
      )}

      <div className="space-y-3">
        {students.map((s) => {
          const pct = s.total > 0 ? Math.round((s.answered / s.total) * 100) : 0;
          const isComplete = s.answered >= s.total;

          return (
            <div key={s.student_id} className="rounded-xl border bg-card p-4">
              <div className="mb-2 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {isComplete ? (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  ) : (
                    <Clock className="h-4 w-4 text-amber-500" />
                  )}
                  <span className="font-medium text-sm">{s.student_name}</span>
                </div>
                <span className="text-sm text-muted-foreground">
                  {s.answered}/{s.total} ({s.correct} {t('correct')})
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    isComplete ? 'bg-green-500' : 'bg-primary'
                  }`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}

        {students.length === 0 && (
          <p className="py-8 text-center text-muted-foreground">{t('noParticipants')}</p>
        )}
      </div>
    </div>
  );
}
