'use client';

import { useTranslations } from 'next-intl';
import { CheckCircle2, XCircle, AlertTriangle, Brain } from 'lucide-react';
import { SubmissionResult } from '@/lib/api/homework';
import { cn } from '@/lib/utils';

interface QuestionFeedbackProps {
  feedback: SubmissionResult;
  showExplanation?: boolean;
}

export function QuestionFeedback({
  feedback,
  showExplanation = true,
}: QuestionFeedbackProps) {
  const t = useTranslations('homework.question');

  const isCorrect = feedback.is_correct === true;
  const isIncorrect = feedback.is_correct === false;
  const isPending = feedback.is_correct === null;

  return (
    <div
      className={cn(
        'rounded-xl p-4 border',
        isCorrect && 'bg-green-50 border-green-200',
        isIncorrect && 'bg-red-50 border-red-200',
        isPending && 'bg-amber-50 border-amber-200'
      )}
    >
      {/* Status Header */}
      <div className="flex items-center gap-2 mb-2">
        {isCorrect ? (
          <>
            <CheckCircle2 className="w-5 h-5 text-green-600" />
            <span className="font-semibold text-green-700">{t('correct')}</span>
          </>
        ) : isIncorrect ? (
          <>
            <XCircle className="w-5 h-5 text-red-600" />
            <span className="font-semibold text-red-700">{t('incorrect')}</span>
          </>
        ) : (
          <>
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            <span className="font-semibold text-amber-700">{t('needsReview')}</span>
          </>
        )}

        {/* Score */}
        <span className="ml-auto text-sm text-gray-600">
          {feedback.score.toFixed(1)}/{feedback.max_score}
        </span>
      </div>

      {/* Feedback text */}
      {feedback.feedback && (
        <p className="text-sm text-gray-700 mb-2">{feedback.feedback}</p>
      )}

      {/* Explanation */}
      {showExplanation && feedback.explanation && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <p className="text-xs text-gray-500 uppercase mb-1">
            {t('explanation')}
          </p>
          <p className="text-sm text-gray-700">{feedback.explanation}</p>
        </div>
      )}

      {/* AI Feedback */}
      {feedback.ai_feedback && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="flex items-center gap-1 mb-1">
            <Brain className="w-3.5 h-3.5 text-purple-500" />
            <p className="text-xs text-purple-600 uppercase">{t('aiFeedback')}</p>
          </div>
          <p className="text-sm text-gray-700">{feedback.ai_feedback}</p>

          {/* AI Confidence */}
          {feedback.ai_confidence !== null && (
            <div className="mt-2 flex items-center gap-2">
              <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={cn(
                    'h-full rounded-full transition-all',
                    feedback.ai_confidence >= 0.7
                      ? 'bg-green-500'
                      : feedback.ai_confidence >= 0.4
                      ? 'bg-amber-500'
                      : 'bg-red-500'
                  )}
                  style={{ width: `${feedback.ai_confidence * 100}%` }}
                />
              </div>
              <span className="text-xs text-gray-500">
                {(feedback.ai_confidence * 100).toFixed(0)}%
              </span>
            </div>
          )}
        </div>
      )}

      {/* Needs review badge */}
      {feedback.needs_review && (
        <div className="mt-3 flex items-center gap-2 text-amber-600">
          <AlertTriangle className="w-4 h-4" />
          <span className="text-sm">{t('needsReview')}</span>
        </div>
      )}
    </div>
  );
}
