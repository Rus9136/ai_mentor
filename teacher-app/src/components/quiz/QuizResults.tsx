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

      {/* Podium — styled top 3 */}
      {leaderboard.length >= 3 && (
        <div className="flex items-end justify-center gap-3 py-4">
          {/* 2nd place (left) */}
          {(() => {
            const p = leaderboard[1];
            return (
              <div className="flex flex-1 max-w-[140px] flex-col items-center">
                <div className="mb-1 text-2xl">{MEDAL[2]}</div>
                <p className="text-sm font-semibold truncate max-w-full">{p.student_name}</p>
                <p className="text-xs text-muted-foreground mb-2">{p.total_score}</p>
                <div className="w-full h-20 rounded-t-lg bg-gradient-to-b from-slate-300 to-slate-400 flex items-center justify-center">
                  <span className="text-xl font-black text-white/80">2</span>
                </div>
              </div>
            );
          })()}
          {/* 1st place (center) */}
          {(() => {
            const p = leaderboard[0];
            return (
              <div className="flex flex-1 max-w-[160px] flex-col items-center">
                <div className="mb-1 text-3xl">{MEDAL[1]}</div>
                <p className="text-base font-bold truncate max-w-full">{p.student_name}</p>
                <p className="text-sm text-muted-foreground mb-2">{p.total_score}</p>
                <div className="w-full h-28 rounded-t-lg bg-gradient-to-b from-yellow-400 to-amber-500 shadow-lg shadow-yellow-400/20 flex items-center justify-center">
                  <span className="text-2xl font-black text-white/90">1</span>
                </div>
              </div>
            );
          })()}
          {/* 3rd place (right) */}
          {(() => {
            const p = leaderboard[2];
            return (
              <div className="flex flex-1 max-w-[140px] flex-col items-center">
                <div className="mb-1 text-2xl">{MEDAL[3]}</div>
                <p className="text-sm font-semibold truncate max-w-full">{p.student_name}</p>
                <p className="text-xs text-muted-foreground mb-2">{p.total_score}</p>
                <div className="w-full h-14 rounded-t-lg bg-gradient-to-b from-amber-600 to-amber-700 flex items-center justify-center">
                  <span className="text-xl font-black text-white/80">3</span>
                </div>
              </div>
            );
          })()}
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
