'use client';

import type { LeaderboardEntry } from '@/types/gamification';

const medals = ['', '\ud83e\udd47', '\ud83e\udd48', '\ud83e\udd49'];
const heights = ['', 'h-24', 'h-20', 'h-16'];
const bgs = ['', 'from-amber-400 to-yellow-300', 'from-slate-300 to-slate-200', 'from-orange-300 to-orange-200'];

interface LeaderboardTopThreeProps {
  entries: LeaderboardEntry[];
}

export function LeaderboardTopThree({ entries }: LeaderboardTopThreeProps) {
  if (entries.length < 1) return null;

  // Display order: 2nd, 1st, 3rd
  const order = [entries[1], entries[0], entries[2]].filter(Boolean);
  if (entries.length < 3) {
    // Less than 3 players — just show in order
    return (
      <div className="flex items-end justify-center gap-3 pb-4">
        {entries.map((entry) => (
          <TopCard key={entry.student_id} entry={entry} />
        ))}
      </div>
    );
  }

  return (
    <div className="flex items-end justify-center gap-2 pb-4">
      {order.map((entry) => (
        <TopCard key={entry.student_id} entry={entry} />
      ))}
    </div>
  );
}

function TopCard({ entry }: { entry: LeaderboardEntry }) {
  const rank = entry.rank;
  const medal = medals[rank] || `#${rank}`;
  const bg = bgs[rank] || 'from-gray-200 to-gray-100';
  const height = heights[rank] || 'h-14';

  return (
    <div className="flex flex-col items-center">
      <span className="text-2xl">{medal}</span>
      <div className={`w-20 rounded-t-xl bg-gradient-to-b ${bg} ${height} flex flex-col items-center justify-end pb-2`}>
        <p className="text-xs font-bold text-foreground/80 leading-tight text-center px-1 truncate w-full">
          {entry.student_name}
        </p>
        <p className="text-[10px] text-foreground/60">Lv.{entry.level}</p>
        <p className="text-[10px] font-semibold text-foreground/70">{entry.total_xp.toLocaleString()}</p>
      </div>
    </div>
  );
}
