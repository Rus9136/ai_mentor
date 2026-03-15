'use client';

import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { useMyQuizzes } from '@/lib/hooks/use-quiz-list';
import { Zap, Users, Clock, Trophy, ChevronRight, Play, CheckCircle2 } from 'lucide-react';
import type { StudentQuizListItem } from '@/types/quiz';

const STATUS_CONFIG: Record<string, { label: string; bg: string; text: string; dot: string }> = {
  lobby: { label: 'available', bg: 'bg-green-100', text: 'text-green-700', dot: 'bg-green-500' },
  in_progress: { label: 'inProgress', bg: 'bg-blue-100', text: 'text-blue-700', dot: 'bg-blue-500' },
  finished: { label: 'completed', bg: 'bg-gray-100', text: 'text-gray-600', dot: 'bg-gray-400' },
};

const MODE_LABELS: Record<string, string> = {
  classic: 'live',
  team: 'team',
  self_paced: 'selfPaced',
};

function StatusBadge({ status }: { status: string }) {
  const t = useTranslations('quizWidget');
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.finished;
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${config.bg} ${config.text}`}>
      {status === 'lobby' && <span className={`h-1.5 w-1.5 rounded-full ${config.dot} animate-pulse`} />}
      {t(config.label)}
    </span>
  );
}

function QuizItem({ quiz }: { quiz: StudentQuizListItem }) {
  const t = useTranslations('quizWidget');
  const isFinished = quiz.status === 'finished';
  const isSelfPaced = quiz.mode === 'self_paced';
  const isActive = quiz.status === 'lobby' || quiz.status === 'in_progress';

  // Build the action link
  const getHref = () => {
    if (isFinished) return null;
    // Auto-join with code for self-paced, or go to quiz page for code entry
    if (isSelfPaced) return `/webview/quiz?code=${quiz.join_code}`;
    return `/webview/quiz?code=${quiz.join_code}`;
  };

  const getActionLabel = () => {
    if (isFinished) return null;
    if (quiz.has_joined && isSelfPaced && quiz.answered_count < quiz.question_count) return t('continue');
    if (quiz.has_joined) return t('rejoin');
    return t('join');
  };

  const href = getHref();
  const actionLabel = getActionLabel();

  return (
    <div className="flex items-center gap-3 py-3">
      {/* Icon */}
      <div className={`flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl ${
        isFinished ? 'bg-gray-100' : isSelfPaced ? 'bg-purple-100' : 'bg-primary/10'
      }`}>
        {isFinished ? (
          <CheckCircle2 className="h-5 w-5 text-gray-500" />
        ) : isSelfPaced ? (
          <Clock className="h-5 w-5 text-purple-600" />
        ) : quiz.mode === 'team' ? (
          <Users className="h-5 w-5 text-primary" />
        ) : (
          <Zap className="h-5 w-5 text-primary" />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium text-foreground truncate">
            {quiz.test_title || t('untitled')}
          </p>
          <StatusBadge status={quiz.status} />
        </div>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-xs text-muted-foreground truncate">{quiz.class_name}</span>
          {quiz.mode !== 'classic' && (
            <>
              <span className="text-xs text-muted-foreground">·</span>
              <span className="text-xs text-muted-foreground">{t(MODE_LABELS[quiz.mode] || 'live')}</span>
            </>
          )}
          {isActive && (
            <>
              <span className="text-xs text-muted-foreground">·</span>
              <span className="text-xs text-muted-foreground">
                <Users className="inline h-3 w-3 mr-0.5" />{quiz.participant_count}
              </span>
            </>
          )}
        </div>

        {/* Progress bar for self-paced in progress */}
        {isSelfPaced && quiz.has_joined && !isFinished && quiz.answered_count > 0 && (
          <div className="flex items-center gap-2 mt-1.5">
            <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full bg-purple-500 transition-all"
                style={{ width: `${Math.round((quiz.answered_count / quiz.question_count) * 100)}%` }}
              />
            </div>
            <span className="text-xs text-muted-foreground">
              {quiz.answered_count}/{quiz.question_count}
            </span>
          </div>
        )}

        {/* Results for finished */}
        {isFinished && quiz.has_joined && (
          <div className="flex items-center gap-3 mt-1">
            {quiz.rank && (
              <span className="flex items-center gap-0.5 text-xs font-medium text-amber-600">
                <Trophy className="h-3 w-3" />#{quiz.rank}
              </span>
            )}
            {quiz.correct_answers !== null && (
              <span className="text-xs text-muted-foreground">
                {quiz.correct_answers}/{quiz.question_count}
              </span>
            )}
            {quiz.xp_earned !== null && quiz.xp_earned > 0 && (
              <span className="text-xs font-medium text-primary">+{quiz.xp_earned} XP</span>
            )}
          </div>
        )}
      </div>

      {/* Action button */}
      {href && actionLabel && (
        <Link
          href={href}
          className="flex-shrink-0 rounded-full bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground hover:opacity-90 transition-opacity"
        >
          <Play className="inline h-3 w-3 mr-1" />
          {actionLabel}
        </Link>
      )}
      {isFinished && (
        <ChevronRight className="h-4 w-4 text-muted-foreground flex-shrink-0" />
      )}
    </div>
  );
}

export function MyQuizzesWidget() {
  const t = useTranslations('quizWidget');
  const { data, isLoading } = useMyQuizzes();

  if (isLoading || !data || data.length === 0) {
    return null;
  }

  return (
    <div className="mb-8">
      <div className="card-elevated overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 pb-3">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
              <Zap className="h-4 w-4 text-primary" />
            </div>
            <h3 className="font-semibold text-foreground">{t('title')}</h3>
          </div>
          <Link
            href="/webview/quiz"
            className="text-xs font-medium text-primary hover:underline"
          >
            {t('enterCode')}
          </Link>
        </div>

        {/* Quiz items */}
        <div className="divide-y divide-border px-4">
          {data.map((quiz) => (
            <QuizItem key={quiz.id} quiz={quiz} />
          ))}
        </div>
      </div>
    </div>
  );
}
