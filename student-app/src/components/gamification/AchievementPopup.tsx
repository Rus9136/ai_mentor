'use client';

import { useState, useEffect } from 'react';
import { useLocale, useTranslations } from 'next-intl';
import { useRecentAchievements } from '@/lib/hooks/use-gamification';
import { useGamificationStore } from '@/stores/gamification-store';
import { Button } from '@/components/ui/button';
import type { StudentAchievement } from '@/types/gamification';

export function AchievementPopup() {
  const t = useTranslations('gamification');
  const locale = useLocale();
  const { data: recent } = useRecentAchievements();
  const { seenAchievementIds, markAchievementSeen } = useGamificationStore();
  const [current, setCurrent] = useState<StudentAchievement | null>(null);

  useEffect(() => {
    if (!recent || recent.length === 0) return;
    const unseen = recent.find(
      (a) => a.is_earned && !seenAchievementIds.has(a.achievement.id)
    );
    if (unseen) {
      setCurrent(unseen);
    }
  }, [recent, seenAchievementIds]);

  if (!current) return null;

  const { achievement } = current;
  const name = locale === 'kz' ? achievement.name_kk : achievement.name_ru;
  const desc = locale === 'kz' ? achievement.description_kk : achievement.description_ru;

  const handleClose = () => {
    markAchievementSeen(achievement.id);
    setCurrent(null);
  };

  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-sm animate-in fade-in zoom-in-95 rounded-2xl bg-card p-6 text-center shadow-xl">
        <span className="text-5xl">{achievement.icon}</span>
        <h3 className="mt-3 text-lg font-bold text-foreground">{name}</h3>
        {desc && <p className="mt-1 text-sm text-muted-foreground">{desc}</p>}
        <p className="mt-2 text-sm font-semibold text-primary">
          +{achievement.xp_reward} XP
        </p>
        <Button onClick={handleClose} className="mt-5 w-full rounded-full">
          {t('awesome')}
        </Button>
      </div>
    </div>
  );
}
