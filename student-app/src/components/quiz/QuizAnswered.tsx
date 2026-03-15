'use client';

import { useTranslations } from 'next-intl';
import { CheckCircle2, Loader2 } from 'lucide-react';

interface QuizAnsweredProps {
  score: number | null;
  isCorrect: boolean | null;
  streakBonus?: number;
  currentStreak?: number;
  powerupUsed?: string | null;
  scoreDoubled?: boolean;
  streakProtected?: boolean;
}

export default function QuizAnswered({
  score, isCorrect, streakBonus = 0, currentStreak = 0,
  powerupUsed, scoreDoubled, streakProtected,
}: QuizAnsweredProps) {
  const t = useTranslations('quiz');

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center px-4 text-center">
      {isCorrect !== null ? (
        <>
          <CheckCircle2
            className={`mb-4 h-16 w-16 ${isCorrect ? 'text-green-500' : 'text-red-400'}`}
          />
          <h2 className="mb-2 text-xl font-bold text-foreground">{t('answerSubmitted')}</h2>
          {score !== null && score > 0 && (
            <p className="text-2xl font-bold text-primary">{t('points', { score })}</p>
          )}
          {scoreDoubled && (
            <p className="mt-1 text-sm font-semibold text-purple-500">
              {t('powerups.scoreDoubled')}
            </p>
          )}
          {streakProtected && (
            <p className="mt-1 text-sm font-semibold text-blue-500">
              {t('powerups.streakProtected')}
            </p>
          )}
          {streakBonus > 0 && (
            <p className="mt-1 text-lg font-semibold text-amber-500">
              +{streakBonus} {t('streakBonus')}
            </p>
          )}
          {currentStreak >= 2 && (
            <p className="mt-2 text-base font-medium text-amber-600">
              🔥 {t('streak', { count: currentStreak })}
            </p>
          )}
        </>
      ) : (
        <>
          <Loader2 className="mb-4 h-12 w-12 animate-spin text-primary" />
          <h2 className="text-xl font-bold text-foreground">{t('answerSubmitted')}</h2>
        </>
      )}
      <p className="mt-4 text-sm text-muted-foreground">{t('waiting')}</p>
    </div>
  );
}
