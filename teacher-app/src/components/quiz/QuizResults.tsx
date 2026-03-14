'use client';

import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { Trophy, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Participant {
  rank: number | null;
  student_name: string;
  total_score: number;
  correct_answers: number;
  xp_earned: number;
}

interface QuizResultsProps {
  totalQuestions: number;
  leaderboard: Participant[];
  stats: { average_score?: number; total_participants?: number };
}

const MEDAL: Record<number, string> = { 1: '🥇', 2: '🥈', 3: '🥉' };

export default function QuizResults({ totalQuestions, leaderboard, stats }: QuizResultsProps) {
  const t = useTranslations('quiz');

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold">{t('results')}</h2>

      {/* Stats */}
      {stats.average_score !== undefined && (
        <div className="flex gap-4">
          <div className="rounded-xl border bg-card px-4 py-3">
            <p className="text-sm text-muted-foreground">{t('averageScore')}</p>
            <p className="text-xl font-bold">{stats.average_score}</p>
          </div>
          <div className="rounded-xl border bg-card px-4 py-3">
            <p className="text-sm text-muted-foreground">{t('participants', { count: stats.total_participants || 0 })}</p>
            <p className="text-xl font-bold">{stats.total_participants || 0}</p>
          </div>
        </div>
      )}

      {/* Top 3 */}
      {leaderboard.length >= 3 && (
        <div className="flex items-end justify-center gap-4 py-4">
          {[1, 0, 2].map((idx) => {
            const p = leaderboard[idx];
            if (!p) return null;
            const isFirst = idx === 0;
            return (
              <div key={idx} className={`text-center ${isFirst ? 'order-2' : idx === 1 ? 'order-1' : 'order-3'}`}>
                <div className="text-2xl">{MEDAL[p.rank || idx + 1]}</div>
                <p className={`font-semibold ${isFirst ? 'text-lg' : 'text-sm'}`}>{p.student_name}</p>
                <p className="text-sm text-muted-foreground">{p.total_score}</p>
              </div>
            );
          })}
        </div>
      )}

      {/* Full table */}
      <div className="overflow-hidden rounded-xl border">
        <table className="w-full">
          <thead className="bg-muted/50">
            <tr className="text-left text-sm">
              <th className="px-4 py-2">{t('rank')}</th>
              <th className="px-4 py-2">—</th>
              <th className="px-4 py-2">{t('score')}</th>
              <th className="px-4 py-2">{t('correctAnswers')}</th>
              <th className="px-4 py-2">{t('xpEarned')}</th>
            </tr>
          </thead>
          <tbody>
            {leaderboard.map((p, i) => (
              <tr key={i} className="border-t text-sm">
                <td className="px-4 py-2 font-medium">{MEDAL[p.rank || 0] || `#${p.rank}`}</td>
                <td className="px-4 py-2">{p.student_name}</td>
                <td className="px-4 py-2 font-semibold">{p.total_score}</td>
                <td className="px-4 py-2">{p.correct_answers}/{totalQuestions}</td>
                <td className="px-4 py-2 text-amber-600">+{p.xp_earned}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Actions */}
      <Link href="/quiz/create">
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          {t('newQuiz')}
        </Button>
      </Link>
    </div>
  );
}
