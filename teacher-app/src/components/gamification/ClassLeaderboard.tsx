'use client';

import { useTranslations } from 'next-intl';
import { useClassLeaderboard } from '@/lib/hooks/use-gamification';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2, Trophy, Flame } from 'lucide-react';
import { cn } from '@/lib/utils';

const MEDAL_COLORS = [
  'bg-yellow-100 text-yellow-700 border-yellow-300',
  'bg-gray-100 text-gray-600 border-gray-300',
  'bg-orange-100 text-orange-700 border-orange-300',
];

const MEDAL_ICONS = ['🥇', '🥈', '🥉'];

export function ClassLeaderboard({ classId }: { classId: number }) {
  const t = useTranslations('gamification');
  const { data, isLoading, error } = useClassLeaderboard(classId);

  if (isLoading) {
    return (
      <div className="flex min-h-[200px] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex min-h-[200px] items-center justify-center text-muted-foreground">
        {t('loadError')}
      </div>
    );
  }

  if (data.entries.length === 0) {
    return (
      <div className="flex min-h-[200px] flex-col items-center justify-center text-muted-foreground">
        <Trophy className="h-10 w-10 mb-2 opacity-50" />
        <p>{t('noData')}</p>
      </div>
    );
  }

  const topThree = data.entries.slice(0, 3);
  const rest = data.entries.slice(3);

  return (
    <div className="space-y-4">
      {/* Top 3 cards */}
      <div className="grid gap-3 md:grid-cols-3">
        {topThree.map((entry, index) => (
          <Card
            key={entry.student_id}
            className={cn('border-2', MEDAL_COLORS[index])}
          >
            <CardContent className="pt-4 pb-4 text-center">
              <span className="text-2xl">{MEDAL_ICONS[index]}</span>
              <p className="mt-1 font-semibold truncate">{entry.student_name}</p>
              <p className="text-sm opacity-75">
                {t('level')} {entry.level}
              </p>
              <p className="mt-1 text-lg font-bold">{entry.total_xp.toLocaleString()} XP</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Rest of the leaderboard */}
      {rest.length > 0 && (
        <Card>
          <CardContent className="pt-4">
            <div className="overflow-x-auto">
              <table className="data-table w-full">
                <thead>
                  <tr>
                    <th className="w-16">#</th>
                    <th>{t('student')}</th>
                    <th className="text-center">{t('level')}</th>
                    <th className="text-right">XP</th>
                  </tr>
                </thead>
                <tbody>
                  {rest.map((entry) => (
                    <tr key={entry.student_id}>
                      <td className="font-medium text-muted-foreground">{entry.rank}</td>
                      <td className="font-medium">{entry.student_name}</td>
                      <td className="text-center">{entry.level}</td>
                      <td className="text-right font-semibold">
                        {entry.total_xp.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Total students */}
      <p className="text-sm text-muted-foreground text-center">
        {t('totalStudents')}: {data.total_students}
      </p>
    </div>
  );
}
