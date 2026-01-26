'use client';

import { useTranslations } from 'next-intl';
import {
  Clock,
  ClipboardList,
  PlayCircle,
  RotateCcw,
  CheckCircle2,
  Trophy,
  Target,
} from 'lucide-react';
import { AvailableTest } from '@/lib/api/tests';
import { TestTypeBadge } from './TestTypeBadge';
import { DifficultyBadge } from './DifficultyBadge';
import { cn } from '@/lib/utils';

interface TestCardProps {
  test: AvailableTest;
  onStart: () => void;
  disabled?: boolean;
}

export function TestCard({ test, onStart, disabled }: TestCardProps) {
  const t = useTranslations('tests.card');

  const hasAttempts = test.attempts_count > 0;
  const hasPassed = test.best_score !== null && test.best_score >= test.passing_score;
  const scorePercentage = test.best_score !== null ? Math.round(test.best_score * 100) : null;
  const passingPercentage = Math.round(test.passing_score * 100);

  const getActionButton = () => {
    if (!test.can_retake && hasAttempts) {
      return (
        <button
          onClick={onStart}
          disabled={disabled}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium bg-primary/10 text-primary hover:bg-primary/20 transition-colors"
        >
          <CheckCircle2 className="w-4 h-4" />
          {t('viewResults')}
        </button>
      );
    }

    if (hasAttempts) {
      return (
        <button
          onClick={onStart}
          disabled={disabled}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
        >
          <RotateCcw className="w-4 h-4" />
          {t('retake')}
        </button>
      );
    }

    return (
      <button
        onClick={onStart}
        disabled={disabled}
        className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium bg-primary text-white hover:bg-primary/90 transition-colors"
      >
        <PlayCircle className="w-4 h-4" />
        {t('start')}
      </button>
    );
  };

  return (
    <div
      className={cn(
        'rounded-xl border-2 p-4 transition-all bg-white',
        hasPassed
          ? 'border-green-200 bg-green-50/50'
          : hasAttempts
          ? 'border-amber-200 bg-amber-50/30'
          : 'border-gray-200'
      )}
    >
      <div className="flex items-start gap-4">
        {/* Icon */}
        <div
          className={cn(
            'w-12 h-12 rounded-xl flex items-center justify-center shrink-0',
            hasPassed
              ? 'bg-green-100 text-green-600'
              : hasAttempts
              ? 'bg-amber-100 text-amber-600'
              : 'bg-gray-100 text-gray-500'
          )}
        >
          {hasPassed ? (
            <Trophy className="w-6 h-6" />
          ) : (
            <ClipboardList className="w-6 h-6" />
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Title and badges */}
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <h4 className="font-semibold text-gray-900">{test.title}</h4>
            <TestTypeBadge type={test.test_purpose} />
            <DifficultyBadge difficulty={test.difficulty} />
          </div>

          {/* Description */}
          {test.description && (
            <p className="text-sm text-gray-500 line-clamp-2 mb-2">{test.description}</p>
          )}

          {/* Meta Info */}
          <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
            {/* Questions */}
            <div className="flex items-center gap-1">
              <ClipboardList className="w-3.5 h-3.5" />
              <span>{t('questions', { count: test.question_count })}</span>
            </div>

            {/* Time Limit */}
            {test.time_limit && (
              <div className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" />
                <span>{t('timeLimit', { minutes: test.time_limit })}</span>
              </div>
            )}

            {/* Passing Score */}
            <div className="flex items-center gap-1">
              <Target className="w-3.5 h-3.5" />
              <span>{t('passingScore', { score: passingPercentage })}</span>
            </div>

            {/* Attempts */}
            {test.attempts_count > 0 && (
              <div className="flex items-center gap-1">
                <RotateCcw className="w-3.5 h-3.5" />
                <span>{t('attempts', { count: test.attempts_count })}</span>
              </div>
            )}
          </div>

          {/* Score display */}
          {hasAttempts && scorePercentage !== null && (
            <div className="mt-3">
              {/* Progress bar */}
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={cn(
                    'h-full transition-all duration-300',
                    hasPassed ? 'bg-green-500' : 'bg-amber-500'
                  )}
                  style={{ width: `${scorePercentage}%` }}
                />
              </div>
              <div className="flex justify-between text-xs mt-1">
                <span className={cn('font-medium', hasPassed ? 'text-green-600' : 'text-amber-600')}>
                  {t('bestScore', { score: scorePercentage })}
                </span>
                {test.latest_score !== null && test.latest_score !== test.best_score && (
                  <span className="text-gray-500">
                    {t('latestScore', { score: Math.round(test.latest_score * 100) })}
                  </span>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Action Button */}
        <div className="shrink-0">{getActionButton()}</div>
      </div>
    </div>
  );
}
