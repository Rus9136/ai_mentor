'use client';

import { useTranslations } from 'next-intl';
import { Button } from '@/components/ui/button';
import { ChevronRight, Square } from 'lucide-react';

interface StudentStatus {
  student_name: string;
  answered: boolean;
}

interface QuizLiveProgressProps {
  currentQuestion: number;
  totalQuestions: number;
  answeredCount: number;
  totalParticipants: number;
  students: StudentStatus[];
  onNextQuestion: () => void;
  onEndQuiz: () => void;
}

export default function QuizLiveProgress({
  currentQuestion,
  totalQuestions,
  answeredCount,
  totalParticipants,
  students,
  onNextQuestion,
  onEndQuiz,
}: QuizLiveProgressProps) {
  const t = useTranslations('quiz');
  const pct = totalParticipants > 0 ? Math.round((answeredCount / totalParticipants) * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">
          {t('questionOf', { current: currentQuestion, total: totalQuestions })}
        </h2>
        <span className="rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-700">
          {t('inProgress')}
        </span>
      </div>

      {/* Answer progress */}
      <div className="rounded-xl border bg-card p-4">
        <p className="mb-2 text-sm font-medium">
          {t('answered', { count: answeredCount, total: totalParticipants })}
        </p>
        <div className="h-3 w-full overflow-hidden rounded-full bg-muted">
          <div
            className="h-full rounded-full bg-primary transition-all duration-300"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {/* Student grid */}
      <div className="rounded-xl border bg-card p-4">
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4">
          {students.map((s, i) => (
            <div
              key={i}
              className={`rounded-lg px-3 py-2 text-center text-sm font-medium ${
                s.answered
                  ? 'border border-green-200 bg-green-50 text-green-700'
                  : 'border border-muted bg-muted/30 text-muted-foreground'
              }`}
            >
              {s.student_name}
              <span className="ml-1">{s.answered ? '✓' : '⏳'}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <Button onClick={onNextQuestion} className="flex-1">
          <ChevronRight className="mr-1 h-4 w-4" />
          {t('nextQuestion')}
        </Button>
        <Button variant="outline" onClick={onEndQuiz}>
          <Square className="mr-1 h-4 w-4" />
          {t('endQuiz')}
        </Button>
      </div>
    </div>
  );
}
