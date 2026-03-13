'use client';

import { useLocale } from 'next-intl';
import type { StudentAchievement } from '@/types/gamification';

const rarityColors: Record<string, string> = {
  common: 'border-gray-300',
  rare: 'border-blue-400',
  epic: 'border-violet-500',
  legendary: 'border-amber-400',
};

const rarityBg: Record<string, string> = {
  common: 'bg-gray-50',
  rare: 'bg-blue-50',
  epic: 'bg-violet-50',
  legendary: 'bg-amber-50',
};

interface AchievementCardProps {
  data: StudentAchievement;
}

export function AchievementCard({ data }: AchievementCardProps) {
  const locale = useLocale();
  const { achievement, is_earned, progress, earned_at } = data;
  const name = locale === 'kz' ? achievement.name_kk : achievement.name_ru;
  const rarity = achievement.rarity;
  const borderColor = rarityColors[rarity] || rarityColors.common;
  const bg = rarityBg[rarity] || rarityBg.common;

  return (
    <div
      className={`relative flex flex-col items-center rounded-xl border-2 p-3 text-center transition-all ${borderColor} ${
        is_earned ? bg : 'border-dashed bg-muted/30 opacity-70'
      }`}
    >
      <span className={`text-2xl ${is_earned ? '' : 'grayscale'}`}>{achievement.icon}</span>
      <p className={`mt-1.5 text-xs font-semibold leading-tight ${is_earned ? 'text-foreground' : 'text-muted-foreground'}`}>
        {name}
      </p>
      {is_earned && earned_at ? (
        <p className="mt-1 text-[10px] text-muted-foreground">
          {new Date(earned_at).toLocaleDateString()}
        </p>
      ) : (
        <div className="mt-2 w-full">
          <div className="h-1 overflow-hidden rounded-full bg-muted">
            <div
              className="h-1 rounded-full bg-primary/60 transition-all"
              style={{ width: `${Math.min(progress * 100, 100)}%` }}
            />
          </div>
          <p className="mt-0.5 text-[10px] text-muted-foreground">
            {Math.round(progress * 100)}%
          </p>
        </div>
      )}
    </div>
  );
}
