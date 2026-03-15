'use client';

import { useTranslations } from 'next-intl';
import { CheckCircle, XCircle, ArrowRight, Loader2 } from 'lucide-react';
import type { SelfPacedAnswerResult } from '@/types/quiz';

interface QuizSelfPacedFeedbackProps {
  result: SelfPacedAnswerResult;
  options: string[];
  onNext: () => void;
  loading?: boolean;
}

const OPTION_LABELS = ['A', 'B', 'C', 'D'];

export default function QuizSelfPacedFeedback({ result, options, onNext, loading }: QuizSelfPacedFeedbackProps) {
  const t = useTranslations('quiz');

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center px-4 py-6">
      {/* Correct / Incorrect indicator */}
      <div className="mb-6">
        {result.is_correct ? (
          <div className="flex flex-col items-center">
            <CheckCircle className="mb-2 h-16 w-16 text-green-500" />
            <p className="text-xl font-bold text-green-600">{t('correct')}</p>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <XCircle className="mb-2 h-16 w-16 text-red-500" />
            <p className="text-xl font-bold text-red-600">{t('incorrect')}</p>
          </div>
        )}
      </div>

      {/* Show correct answer */}
      <div className="mb-6 w-full max-w-sm space-y-2">
        {options.map((option, i) => (
          <div
            key={i}
            className={`rounded-xl px-4 py-3 text-sm font-medium ${
              i === result.correct_option
                ? 'bg-green-100 text-green-800 ring-2 ring-green-500'
                : 'bg-muted text-muted-foreground'
            }`}
          >
            <span className="mr-2 font-bold">{OPTION_LABELS[i]}.</span>
            {option}
            {i === result.correct_option && ' ✓'}
          </div>
        ))}
      </div>

      {/* Progress */}
      <p className="mb-4 text-sm text-muted-foreground">
        {result.answered_count} / {result.total_questions} {t('questions')}
      </p>
      <p className="mb-6 text-sm text-muted-foreground">
        {t('score')}: {result.total_score} | {t('correctAnswers', { correct: result.correct_answers, total: result.total_questions })}
      </p>

      {/* Next button */}
      <button
        onClick={onNext}
        disabled={loading}
        className="flex items-center gap-2 rounded-xl bg-primary px-8 py-3 text-lg font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
      >
        {loading ? (
          <Loader2 className="h-5 w-5 animate-spin" />
        ) : (
          <>
            {result.is_finished ? t('finished') : t('nextQuestion')}
            <ArrowRight className="h-5 w-5" />
          </>
        )}
      </button>
    </div>
  );
}
