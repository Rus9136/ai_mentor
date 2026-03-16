'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import type { LeaderboardEntry, TeamEntry } from '@/types/quiz';
import QuizMiniLeaderboard from './QuizMiniLeaderboard';

interface QuizQuestionResultProps {
  correctOption: number | null;
  stats: Record<string, number>;
  options: string[];
  leaderboardTop5: LeaderboardEntry[];
  teamLeaderboard?: TeamEntry[];
  autoAdvanceMs?: number | null;
}

const BAR_COLORS = ['bg-red-500', 'bg-blue-500', 'bg-amber-500', 'bg-green-500'];
const OPTION_LABELS = ['A', 'B', 'C', 'D'];

export default function QuizQuestionResult({ correctOption, stats, options, leaderboardTop5, teamLeaderboard, autoAdvanceMs }: QuizQuestionResultProps) {
  const t = useTranslations('quiz');
  const maxCount = Math.max(1, ...Object.values(stats));

  // Auto-advance countdown
  const [countdown, setCountdown] = useState<number | null>(
    autoAdvanceMs ? Math.ceil(autoAdvanceMs / 1000) : null,
  );
  useEffect(() => {
    if (!autoAdvanceMs) return;
    setCountdown(Math.ceil(autoAdvanceMs / 1000));
    const interval = setInterval(() => {
      setCountdown((prev) => (prev !== null && prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(interval);
  }, [autoAdvanceMs]);

  return (
    <div className="flex min-h-dvh flex-col items-center px-4 py-6">
      <h2 className="mb-6 text-lg font-bold text-foreground">{t('correctAnswer')}</h2>

      {/* Answer distribution */}
      <div className="mb-8 w-full max-w-sm space-y-3">
        {options.map((option, i) => {
          const count = stats[String(i)] || 0;
          const pct = Math.round((count / maxCount) * 100);
          const isCorrect = i === correctOption;

          return (
            <div key={i} className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className={`font-medium ${isCorrect ? 'text-green-600' : 'text-foreground'}`}>
                  {OPTION_LABELS[i]}. {option} {isCorrect && '✓'}
                </span>
                <span className="text-muted-foreground">{count}</span>
              </div>
              <div className="h-3 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    isCorrect ? 'bg-green-500' : BAR_COLORS[i]
                  }`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Team leaderboard (if team mode) */}
      {teamLeaderboard && teamLeaderboard.length > 0 && (
        <div className="mb-4 w-full max-w-sm space-y-2">
          <h3 className="text-sm font-semibold text-muted-foreground">{t('teamStandings')}</h3>
          {teamLeaderboard.map((team, i) => (
            <div key={team.id} className="flex items-center justify-between rounded-lg px-3 py-2 bg-card">
              <div className="flex items-center gap-2">
                <span className="h-3 w-3 rounded-full" style={{ backgroundColor: team.color }} />
                <span className="text-sm font-medium">{team.name}</span>
              </div>
              <span className="text-sm font-bold">{team.total_score}</span>
            </div>
          ))}
        </div>
      )}

      {/* Mini leaderboard */}
      <QuizMiniLeaderboard entries={leaderboardTop5} />

      {countdown !== null && countdown > 0 ? (
        <p className="mt-6 text-sm font-medium text-primary">{t('nextQuestionIn', { sec: countdown })}</p>
      ) : (
        <p className="mt-6 text-sm text-muted-foreground">{t('waiting')}</p>
      )}
    </div>
  );
}
