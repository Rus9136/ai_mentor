'use client';

import { useTranslations } from 'next-intl';
import { useAchievements } from '@/lib/hooks/use-gamification';
import { AchievementCard } from './AchievementCard';
import { Trophy, Loader2 } from 'lucide-react';

export function AchievementGrid() {
  const t = useTranslations('gamification');
  const { data: achievements, isLoading } = useAchievements();

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!achievements || achievements.length === 0) {
    return (
      <div className="py-12 text-center">
        <Trophy className="mx-auto h-10 w-10 text-muted-foreground/40" />
        <p className="mt-2 text-sm text-muted-foreground">{t('noAchievements')}</p>
        <p className="text-xs text-muted-foreground">{t('keepLearning')}</p>
      </div>
    );
  }

  // Sort: earned first (by date desc), then by progress desc
  const sorted = [...achievements].sort((a, b) => {
    if (a.is_earned && !b.is_earned) return -1;
    if (!a.is_earned && b.is_earned) return 1;
    if (a.is_earned && b.is_earned) {
      return new Date(b.earned_at!).getTime() - new Date(a.earned_at!).getTime();
    }
    return b.progress - a.progress;
  });

  return (
    <div className="grid grid-cols-3 gap-3 sm:grid-cols-4 lg:grid-cols-5">
      {sorted.map((ach) => (
        <AchievementCard key={ach.achievement.id} data={ach} />
      ))}
    </div>
  );
}
