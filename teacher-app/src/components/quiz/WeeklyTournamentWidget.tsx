'use client';

import { useTranslations } from 'next-intl';
import { useQuery } from '@tanstack/react-query';
import { Trophy, Calendar } from 'lucide-react';
import { Link } from '@/i18n/routing';
import { apiClient } from '@/lib/api/client';

interface Tournament {
  id: number;
  class_id: number;
  quiz_session_id: number | null;
  week_start: string;
  week_end: string;
  status: string;
}

async function getTournaments(): Promise<Tournament[]> {
  const res = await apiClient.get('/teachers/quiz-sessions/tournaments');
  return res.data;
}

const STATUS_COLORS: Record<string, string> = {
  scheduled: 'bg-blue-100 text-blue-700',
  active: 'bg-green-100 text-green-700',
  finished: 'bg-gray-100 text-gray-600',
  cancelled: 'bg-red-100 text-red-600',
};

export default function WeeklyTournamentWidget() {
  const t = useTranslations('quiz');
  const { data: tournaments = [] } = useQuery({
    queryKey: ['quiz', 'tournaments'],
    queryFn: getTournaments,
    refetchInterval: 30000,
  });

  if (tournaments.length === 0) return null;

  return (
    <div className="rounded-xl border bg-card p-4">
      <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-muted-foreground">
        <Trophy className="h-4 w-4 text-amber-500" />
        {t('tournament')}
      </h3>
      <div className="space-y-2">
        {tournaments.map((t_item) => (
          <div
            key={t_item.id}
            className="flex items-center justify-between rounded-lg border px-3 py-2"
          >
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm">
                {t_item.week_start} — {t_item.week_end}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[t_item.status] || ''}`}>
                {t_item.status === 'active' ? t('tournamentActive') : t('tournamentFinished')}
              </span>
              {t_item.quiz_session_id && (
                <Link
                  href={`/quiz/${t_item.quiz_session_id}`}
                  className="text-xs text-primary hover:underline"
                >
                  →
                </Link>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
