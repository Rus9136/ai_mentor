'use client';

import { useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { Trophy, Star, Zap } from 'lucide-react';
import type { QuizFinishedData } from '@/types/quiz';

interface QuizFinishedProps {
  data: QuizFinishedData;
}

const MEDAL_EMOJI: Record<number, string> = { 1: '🥇', 2: '🥈', 3: '🥉' };

export default function QuizFinished({ data }: QuizFinishedProps) {
  const t = useTranslations('quiz');

  useEffect(() => {
    if (data.your_rank && data.your_rank <= 3) {
      import('canvas-confetti').then((confetti) => {
        confetti.default({
          particleCount: 100,
          spread: 70,
          origin: { y: 0.6 },
        });
      });
    }
  }, [data.your_rank]);

  return (
    <div className="flex min-h-dvh flex-col items-center px-4 py-6">
      <h1 className="mb-6 text-2xl font-bold text-foreground">{t('finished')}</h1>

      {/* Your result */}
      <div className="mb-6 w-full max-w-sm rounded-2xl bg-card p-6 text-center shadow-lg">
        {data.your_rank && (
          <div className="mb-2 text-4xl">
            {MEDAL_EMOJI[data.your_rank] || `#${data.your_rank}`}
          </div>
        )}
        <p className="mb-1 text-lg font-semibold text-foreground">
          {t('yourRank', { rank: data.your_rank || '-' })}
        </p>
        <div className="flex items-center justify-center gap-4 text-sm text-muted-foreground">
          <span className="flex items-center gap-1">
            <Star className="h-4 w-4 text-primary" />
            {data.your_score} {t('score')}
          </span>
          <span className="flex items-center gap-1">
            <Zap className="h-4 w-4 text-amber-500" />
            +{data.xp_earned} XP
          </span>
        </div>
        <p className="mt-2 text-sm text-muted-foreground">
          {t('correctAnswers', { correct: data.correct_answers, total: data.total_questions })}
        </p>
      </div>

      {/* Team leaderboard (if team mode) */}
      {data.team_leaderboard && data.team_leaderboard.length > 0 && (
        <div className="mb-6 w-full max-w-sm">
          <h3 className="mb-3 text-sm font-semibold text-muted-foreground">{t('teamStandings')}</h3>
          <div className="space-y-2">
            {data.team_leaderboard.map((team, i) => (
              <div key={team.id} className="flex items-center justify-between rounded-xl px-4 py-3 bg-card">
                <div className="flex items-center gap-3">
                  <span className="text-lg font-bold text-muted-foreground">#{i + 1}</span>
                  <span className="h-4 w-4 rounded-full" style={{ backgroundColor: team.color }} />
                  <span className="font-medium text-foreground">{team.name}</span>
                </div>
                <span className="font-bold text-foreground">{team.total_score}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Full leaderboard */}
      <div className="w-full max-w-sm">
        <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-muted-foreground">
          <Trophy className="h-4 w-4" />
          {t('leaderboard')}
        </h3>
        <div className="space-y-2">
          {data.leaderboard.map((entry) => (
            <div
              key={entry.rank}
              className={`flex items-center justify-between rounded-xl px-4 py-3 ${
                entry.rank === data.your_rank ? 'bg-primary/10 ring-2 ring-primary' : 'bg-card'
              }`}
            >
              <div className="flex items-center gap-3">
                <span className="w-6 text-center text-sm font-bold text-muted-foreground">
                  {MEDAL_EMOJI[entry.rank] || `${entry.rank}`}
                </span>
                <span className="text-sm font-medium text-foreground">{entry.student_name}</span>
              </div>
              <div className="text-right">
                <span className="text-sm font-bold text-foreground">{entry.total_score}</span>
                {entry.xp_earned ? (
                  <span className="ml-2 text-xs text-amber-500">+{entry.xp_earned} XP</span>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
