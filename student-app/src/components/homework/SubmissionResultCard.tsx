'use client';

import { useTranslations } from 'next-intl';
import { CheckCircle2, XCircle, AlertTriangle, Award, Clock, FileText, Brain } from 'lucide-react';
import { TaskSubmissionResult, TaskType } from '@/lib/api/homework';
import { cn } from '@/lib/utils';

// Task types that don't show correct/incorrect stats (AI-graded open tasks)
const OPEN_TASK_TYPES = [TaskType.PRACTICE, TaskType.ESSAY, TaskType.OPEN_QUESTION];

interface SubmissionResultCardProps {
  result: TaskSubmissionResult;
  taskType?: TaskType;
  onBackToHomework: () => void;
  onTryAgain?: () => void;
  canTryAgain?: boolean;
}

export function SubmissionResultCard({
  result,
  taskType,
  onBackToHomework,
  onTryAgain,
  canTryAgain,
}: SubmissionResultCardProps) {
  const t = useTranslations('homework.result');

  const isPassed = result.percentage >= 60;

  // Open task types (essay, practice, open_question) don't show correct/incorrect stats
  const isOpenTask = taskType && OPEN_TASK_TYPES.includes(taskType);

  // For open tasks, check if all answers need review (not yet graded by teacher)
  const isPendingReview = isOpenTask && result.needs_review_count > 0;

  return (
    <div className="card-elevated overflow-hidden">
      {/* Header */}
      <div
        className={cn(
          'px-6 py-8 text-center',
          isOpenTask
            ? isPendingReview
              ? 'bg-gradient-to-r from-amber-50 to-orange-50'
              : 'bg-gradient-to-r from-blue-50 to-indigo-50'
            : isPassed
              ? 'bg-gradient-to-r from-green-50 to-emerald-50'
              : 'bg-gradient-to-r from-red-50 to-orange-50'
        )}
      >
        <div
          className={cn(
            'w-16 h-16 rounded-full mx-auto mb-4 flex items-center justify-center',
            isOpenTask
              ? isPendingReview
                ? 'bg-amber-100'
                : 'bg-blue-100'
              : isPassed
                ? 'bg-green-100'
                : 'bg-red-100'
          )}
        >
          {isOpenTask ? (
            isPendingReview ? (
              <AlertTriangle className="w-8 h-8 text-amber-600" />
            ) : (
              <FileText className="w-8 h-8 text-blue-600" />
            )
          ) : isPassed ? (
            <CheckCircle2 className="w-8 h-8 text-green-600" />
          ) : (
            <XCircle className="w-8 h-8 text-red-600" />
          )}
        </div>

        <h3 className="text-2xl font-bold text-gray-900 mb-2">{t('title')}</h3>

        <p
          className={cn(
            'text-lg font-medium',
            isOpenTask
              ? isPendingReview
                ? 'text-amber-600'
                : 'text-blue-600'
              : isPassed
                ? 'text-green-600'
                : 'text-red-600'
          )}
        >
          {isOpenTask
            ? isPendingReview
              ? t('pendingReview')
              : t('submitted')
            : isPassed
              ? t('passed')
              : t('failed')}
        </p>
      </div>

      {/* Stats */}
      <div className="px-6 py-6 space-y-4">
        {/* Score */}
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
          <div className="flex items-center gap-3">
            <Award className="w-5 h-5 text-primary" />
            <span className="font-medium text-gray-700">{t('score')}</span>
          </div>
          <div className="text-right">
            <span className="text-2xl font-bold text-gray-900">
              {result.total_score.toFixed(1)}
            </span>
            <span className="text-gray-500">/{result.max_score}</span>
            <p className="text-sm text-primary font-medium">
              {t('percentage', { percent: result.percentage.toFixed(0) })}
            </p>
          </div>
        </div>

        {/* Correct/Incorrect - only for quiz/test tasks */}
        {!isOpenTask && (
          <div className="grid grid-cols-2 gap-3">
            <div className="flex items-center gap-3 p-3 bg-green-50 rounded-xl">
              <CheckCircle2 className="w-5 h-5 text-green-600" />
              <div>
                <p className="text-lg font-bold text-green-700">
                  {result.correct_count}
                </p>
                <p className="text-xs text-green-600">{t('correct')}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 bg-red-50 rounded-xl">
              <XCircle className="w-5 h-5 text-red-600" />
              <div>
                <p className="text-lg font-bold text-red-700">
                  {result.incorrect_count}
                </p>
                <p className="text-xs text-red-600">{t('incorrect')}</p>
              </div>
            </div>
          </div>
        )}

        {/* AI Feedback summary for open tasks */}
        {isOpenTask && (
          <div className="flex items-center gap-3 p-4 bg-purple-50 rounded-xl">
            <Brain className="w-5 h-5 text-purple-600" />
            <div>
              <p className="text-sm font-medium text-purple-700">
                {t('aiEvaluated')}
              </p>
              <p className="text-xs text-purple-600">
                {t('aiEvaluatedDescription')}
              </p>
            </div>
          </div>
        )}

        {/* Needs Review */}
        {result.needs_review_count > 0 && (
          <div className="flex items-center gap-3 p-3 bg-amber-50 rounded-xl">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            <div>
              <p className="text-sm font-medium text-amber-700">
                {result.needs_review_count} {t('needsReview')}
              </p>
            </div>
          </div>
        )}

        {/* Late Penalty */}
        {result.is_late && result.late_penalty_applied > 0 && (
          <div className="flex items-center justify-between p-3 bg-red-50 rounded-xl">
            <div className="flex items-center gap-3">
              <Clock className="w-5 h-5 text-red-600" />
              <span className="font-medium text-red-700">{t('latePenalty')}</span>
            </div>
            <span className="text-red-600 font-medium">
              -{result.late_penalty_applied.toFixed(0)}%
            </span>
          </div>
        )}

        {/* Original Score (if late) */}
        {result.original_score !== null && result.original_score !== result.total_score && (
          <p className="text-sm text-gray-500 text-center">
            {t('originalScore')}: {result.original_score.toFixed(1)}
          </p>
        )}

        {/* Attempt Info */}
        <p className="text-sm text-gray-500 text-center">
          {t('attempt', { number: result.attempt_number })}
        </p>
      </div>

      {/* Actions */}
      <div className="px-6 pb-6 flex flex-col gap-3">
        {canTryAgain && onTryAgain && (
          <button
            onClick={onTryAgain}
            className="w-full py-3 rounded-xl font-medium bg-primary text-white hover:bg-primary/90 transition-colors"
          >
            {t('tryAgain')}
          </button>
        )}
        <button
          onClick={onBackToHomework}
          className="w-full py-3 rounded-xl font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
        >
          {t('backToHomework')}
        </button>
      </div>
    </div>
  );
}
