'use client';

import { useTranslations } from 'next-intl';
import { Trophy } from 'lucide-react';
import type { LeaderboardEntry } from '@/types/quiz';

interface QuizMiniLeaderboardProps {
  entries: LeaderboardEntry[];
}

const RANK_STYLES: Record<number, string> = {
  1: 'text-yellow-500',
  2: 'text-gray-400',
  3: 'text-amber-600',
};

export default function QuizMiniLeaderboard({ entries }: QuizMiniLeaderboardProps) {
  const t = useTranslations('quiz');

  if (!entries.length) return null;

  return (
    <div className="w-full max-w-sm rounded-xl bg-card p-4">
      <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-muted-foreground">
        <Trophy className="h-4 w-4" />
        {t('leaderboard')}
      </h3>
      <div className="space-y-2">
        {entries.map((entry) => (
          <div
            key={entry.rank}
            className="flex items-center justify-between rounded-lg bg-muted/50 px-3 py-2"
          >
            <div className="flex items-center gap-2">
              <span className={`text-sm font-bold ${RANK_STYLES[entry.rank] || 'text-muted-foreground'}`}>
                #{entry.rank}
              </span>
              <span className="text-sm font-medium text-foreground">{entry.student_name}</span>
            </div>
            <span className="text-sm font-semibold text-primary">{entry.total_score}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
