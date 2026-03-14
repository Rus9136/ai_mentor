'use client';

import { useTranslations } from 'next-intl';
import type { LeaderboardEntry } from '@/types/quiz';
import QuizMiniLeaderboard from './QuizMiniLeaderboard';

interface QuizQuestionResultProps {
  correctOption: number | null;
  stats: Record<string, number>;
  options: string[];
  leaderboardTop5: LeaderboardEntry[];
}

const BAR_COLORS = ['bg-red-500', 'bg-blue-500', 'bg-amber-500', 'bg-green-500'];
const OPTION_LABELS = ['A', 'B', 'C', 'D'];

export default function QuizQuestionResult({ correctOption, stats, options, leaderboardTop5 }: QuizQuestionResultProps) {
  const t = useTranslations('quiz');
  const maxCount = Math.max(1, ...Object.values(stats));

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

      {/* Mini leaderboard */}
      <QuizMiniLeaderboard entries={leaderboardTop5} />

      <p className="mt-6 text-sm text-muted-foreground">{t('waiting')}</p>
    </div>
  );
}
