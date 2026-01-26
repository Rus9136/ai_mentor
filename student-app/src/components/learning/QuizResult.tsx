'use client';

import { useTranslations } from 'next-intl';
import { cn } from '@/lib/utils';
import { TestAttemptDetail } from '@/lib/api/tests';
import {
  Trophy,
  Target,
  Clock,
  RefreshCw,
  ArrowRight,
  CheckCircle2,
  XCircle,
  MessageCircle,
} from 'lucide-react';

interface QuizResultProps {
  attempt: TestAttemptDetail;
  onRetake: () => void;
  onClose: () => void;
  onOpenChat?: () => void;
  className?: string;
}

export function QuizResult({
  attempt,
  onRetake,
  onClose,
  onOpenChat,
  className,
}: QuizResultProps) {
  const t = useTranslations('paragraph.quiz');

  const score = attempt.score ?? 0;
  const scorePercent = Math.round(score * 100);
  const passed = attempt.passed ?? false;
  const pointsEarned = attempt.points_earned ?? 0;
  const totalPoints = attempt.total_points ?? 0;
  const timeSpent = attempt.time_spent ?? 0;

  // Calculate correct answers count
  const correctCount = attempt.answers.filter(a => a.is_correct).length;
  const totalQuestions = attempt.answers.length;

  // Format time
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    if (mins > 0) {
      return `${mins}m ${secs}s`;
    }
    return `${secs}s`;
  };

  // Get score color
  const getScoreColor = () => {
    if (scorePercent >= 85) return 'text-green-600';
    if (scorePercent >= 60) return 'text-amber-600';
    return 'text-red-600';
  };

  const getScoreBgColor = () => {
    if (scorePercent >= 85) return 'bg-green-100';
    if (scorePercent >= 60) return 'bg-amber-100';
    return 'bg-red-100';
  };

  return (
    <div className={cn('flex flex-col items-center', className)}>
      {/* Trophy / Result Icon */}
      <div className={cn(
        'w-20 h-20 rounded-full flex items-center justify-center mb-6',
        passed ? 'bg-green-100' : 'bg-red-100'
      )}>
        {passed ? (
          <Trophy className="w-10 h-10 text-green-600" />
        ) : (
          <Target className="w-10 h-10 text-red-600" />
        )}
      </div>

      {/* Result Title */}
      <h2 className={cn(
        'text-2xl font-bold mb-2',
        passed ? 'text-green-700' : 'text-red-700'
      )}>
        {passed ? t('result.passed') : t('result.failed')}
      </h2>

      {/* Score */}
      <div className={cn(
        'text-5xl font-bold mb-2',
        getScoreColor()
      )}>
        {scorePercent}%
      </div>

      <p className="text-gray-600 mb-8">
        {t('result.points', { earned: pointsEarned.toFixed(1), total: totalPoints.toFixed(1) })}
      </p>

      {/* Stats Grid */}
      <div className="grid grid-cols-3 gap-4 w-full max-w-md mb-8">
        {/* Correct Answers */}
        <div className={cn(
          'p-4 rounded-xl text-center',
          getScoreBgColor()
        )}>
          <div className="flex justify-center mb-2">
            <CheckCircle2 className={cn('w-6 h-6', getScoreColor())} />
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {correctCount}/{totalQuestions}
          </div>
          <div className="text-xs text-gray-600">
            {t('result.correctAnswers')}
          </div>
        </div>

        {/* Time Spent */}
        <div className="bg-blue-100 p-4 rounded-xl text-center">
          <div className="flex justify-center mb-2">
            <Clock className="w-6 h-6 text-blue-600" />
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {formatTime(timeSpent)}
          </div>
          <div className="text-xs text-gray-600">
            {t('result.timeSpent')}
          </div>
        </div>

        {/* Passing Score */}
        <div className="bg-gray-100 p-4 rounded-xl text-center">
          <div className="flex justify-center mb-2">
            <Target className="w-6 h-6 text-gray-600" />
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {Math.round(attempt.test.passing_score * 100)}%
          </div>
          <div className="text-xs text-gray-600">
            {t('result.passingScore')}
          </div>
        </div>
      </div>

      {/* Question Review */}
      <div className="w-full max-w-md mb-8">
        <h3 className="font-semibold text-gray-900 mb-3">{t('result.questionReview')}</h3>
        <div className="flex flex-wrap gap-2">
          {attempt.answers.map((answer, index) => (
            <div
              key={answer.id}
              className={cn(
                'w-10 h-10 rounded-lg flex items-center justify-center font-medium',
                answer.is_correct
                  ? 'bg-green-100 text-green-700'
                  : 'bg-red-100 text-red-700'
              )}
            >
              {index + 1}
            </div>
          ))}
        </div>
      </div>

      {/* AI Chat for failed attempts */}
      {!passed && (
        <div className="w-full max-w-md mb-8 p-4 bg-purple-50 border border-purple-200 rounded-xl">
          <div className="flex items-center gap-3 mb-2">
            <MessageCircle className="w-5 h-5 text-purple-600" />
            <span className="font-semibold text-purple-700">{t('result.needHelp')}</span>
          </div>
          <p className="text-sm text-purple-600 mb-3">
            {t('result.aiChatHint')}
          </p>
          <button
            onClick={onOpenChat}
            className="w-full py-2 px-4 bg-purple-500 text-white rounded-lg font-medium hover:bg-purple-600 transition-colors"
          >
            {t('result.askAI')}
          </button>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-4 w-full max-w-md">
        {!passed && (
          <button
            onClick={onRetake}
            className="flex-1 flex items-center justify-center gap-2 py-3 px-6 bg-amber-100 text-amber-700 rounded-xl font-medium hover:bg-amber-200 transition-colors"
          >
            <RefreshCw className="w-5 h-5" />
            {t('retake')}
          </button>
        )}
        <button
          onClick={onClose}
          className={cn(
            'flex items-center justify-center gap-2 py-3 px-6 rounded-xl font-medium transition-colors',
            passed
              ? 'flex-1 bg-green-500 text-white hover:bg-green-600'
              : 'flex-1 bg-gray-200 text-gray-700 hover:bg-gray-300'
          )}
        >
          {t('close')}
          <ArrowRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
