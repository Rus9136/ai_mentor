'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { useLeaderboard } from '@/lib/hooks/use-gamification';
import { useStudentProfile } from '@/lib/hooks/use-profile';
import { LeaderboardTopThree } from './LeaderboardTopThree';
import { Loader2 } from 'lucide-react';

export function Leaderboard() {
  const t = useTranslations('gamification');
  const { data: profile } = useStudentProfile();
  const classId = profile?.classes?.[0]?.id;
  const hasClass = !!classId;

  const [scope, setScope] = useState<'school' | 'class'>('school');
  const { data, isLoading } = useLeaderboard(scope, scope === 'class' ? classId : undefined);

  return (
    <div>
      {/* Scope toggle */}
      <div className="mb-4 flex gap-2">
        <ScopeButton active={scope === 'school'} onClick={() => setScope('school')}>
          {t('school')}
        </ScopeButton>
        {hasClass && (
          <ScopeButton active={scope === 'class'} onClick={() => setScope('class')}>
            {t('class')}
          </ScopeButton>
        )}
      </div>

      {isLoading && (
        <div className="flex justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      )}

      {data && (
        <>
          {/* Top 3 podium */}
          <LeaderboardTopThree entries={data.entries.slice(0, 3)} />

          {/* Rest of leaderboard */}
          <div className="mt-2 space-y-1">
            {data.entries.slice(3).map((entry) => {
              const isMe = entry.rank === data.student_rank;
              return (
                <div
                  key={entry.student_id}
                  className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm ${
                    isMe ? 'bg-primary/10 font-bold' : ''
                  }`}
                >
                  <span className="w-6 text-right font-semibold text-muted-foreground">
                    {entry.rank}
                  </span>
                  <span className="min-w-0 flex-1 truncate text-foreground">
                    {entry.student_name}
                  </span>
                  <span className="text-xs text-muted-foreground">Lv.{entry.level}</span>
                  <span className="w-16 text-right font-medium tabular-nums">
                    {entry.total_xp.toLocaleString()}
                  </span>
                </div>
              );
            })}
          </div>

          {/* User position if not in visible list */}
          {data.student_rank > data.entries.length && (
            <div className="mt-3 border-t border-border pt-3">
              <div className="flex items-center gap-3 rounded-lg bg-primary/10 px-3 py-2 text-sm font-bold">
                <span className="w-6 text-right text-muted-foreground">{data.student_rank}</span>
                <span className="flex-1">{t('yourRank', { rank: data.student_rank })}</span>
                <span className="text-xs text-muted-foreground">Lv.{data.student_level}</span>
                <span className="w-16 text-right tabular-nums">{data.student_xp.toLocaleString()}</span>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function ScopeButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full px-4 py-1.5 text-sm font-semibold transition-colors ${
        active
          ? 'bg-primary text-primary-foreground'
          : 'bg-muted text-muted-foreground hover:bg-muted/80'
      }`}
    >
      {children}
    </button>
  );
}
