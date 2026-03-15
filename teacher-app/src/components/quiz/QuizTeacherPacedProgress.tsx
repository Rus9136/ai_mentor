'use client';

import { useTranslations } from 'next-intl';
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight, Square } from 'lucide-react';

interface QuizTeacherPacedProgressProps {
  currentQuestion: number; // 1-based
  totalQuestions: number;
  answeredCount: number;
  totalParticipants: number;
  onGoToQuestion: (index: number) => void; // 0-based
  onNextQuestion: () => void;
  onEndQuiz: () => void;
}

export default function QuizTeacherPacedProgress({
  currentQuestion,
  totalQuestions,
  answeredCount,
  totalParticipants,
  onGoToQuestion,
  onNextQuestion,
  onEndQuiz,
}: QuizTeacherPacedProgressProps) {
  const t = useTranslations('quiz');
  const pct = totalParticipants > 0 ? Math.round((answeredCount / totalParticipants) * 100) : 0;
  const currentIndex = currentQuestion - 1; // 0-based

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">
          {t('questionOf', { current: currentQuestion, total: totalQuestions })}
        </h2>
        <span className="rounded-full bg-blue-100 px-3 py-1 text-sm font-medium text-blue-700">
          {t('teacherPacedPacing')}
        </span>
      </div>

      {/* Question navigator */}
      <div className="rounded-xl border bg-card p-4">
        <div className="flex flex-wrap gap-2">
          {Array.from({ length: totalQuestions }, (_, i) => (
            <button
              key={i}
              onClick={() => onGoToQuestion(i)}
              className={`flex h-9 w-9 items-center justify-center rounded-lg text-sm font-medium transition-colors ${
                i === currentIndex
                  ? 'bg-primary text-primary-foreground'
                  : 'border bg-muted/30 hover:bg-muted'
              }`}
            >
              {i + 1}
            </button>
          ))}
        </div>
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

      {/* Navigation actions */}
      <div className="flex gap-3">
        <Button
          variant="outline"
          onClick={() => onGoToQuestion(currentIndex - 1)}
          disabled={currentIndex <= 0}
        >
          <ChevronLeft className="mr-1 h-4 w-4" />
          {t('previousQuestion')}
        </Button>
        <Button
          onClick={() => {
            if (currentIndex >= totalQuestions - 1) {
              onNextQuestion(); // triggers auto-finish via handle_next_question
            } else {
              onGoToQuestion(currentIndex + 1);
            }
          }}
          className="flex-1"
        >
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
