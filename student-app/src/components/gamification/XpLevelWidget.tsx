'use client';

import { useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { ChevronRight, Star } from 'lucide-react';
import { useGamificationProfile } from '@/lib/hooks/use-gamification';
import { useGamificationStore } from '@/stores/gamification-store';
import { XpProgressBar } from './XpProgressBar';
import { StreakBadge } from './StreakBadge';

export function XpLevelWidget() {
  const t = useTranslations('gamification');
  const { data: profile } = useGamificationProfile();
  const { prevXp, prevLevel, setPrev, showXpToast } = useGamificationStore();

  // XP toast detection
  useEffect(() => {
    if (!profile) return;
    if (prevXp > 0 && profile.total_xp > prevXp) {
      const diff = profile.total_xp - prevXp;
      const levelUp = prevLevel > 0 && profile.level > prevLevel ? profile.level : undefined;
      showXpToast(diff, levelUp);
    }
    setPrev(profile.total_xp, profile.level);
  }, [profile?.total_xp, profile?.level]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!profile) return null;

  return (
    <Link href="/gamification">
      <div className="group card-elevated mb-6 cursor-pointer overflow-hidden p-0 transition-all hover:shadow-soft-lg">
        <div className="flex items-stretch">
          <div className="w-2 bg-gradient-to-b from-violet-500 to-blue-500" />
          <div className="flex flex-1 items-center gap-4 p-4">
            {/* Level badge */}
            <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-blue-500 text-white shadow-sm">
              <div className="text-center leading-tight">
                <Star className="mx-auto h-3.5 w-3.5" />
                <span className="text-sm font-extrabold">{profile.level}</span>
              </div>
            </div>

            {/* XP bar + info */}
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between">
                <span className="text-sm font-bold text-foreground">
                  {t('level')} {profile.level}
                </span>
                <StreakBadge days={profile.current_streak} isActive={profile.current_streak > 0} />
              </div>
              <div className="mt-1.5">
                <XpProgressBar
                  currentXp={profile.xp_in_current_level}
                  xpToNext={profile.xp_to_next_level}
                  level={profile.level}
                  size="sm"
                />
              </div>
            </div>

            <ChevronRight className="h-5 w-5 flex-shrink-0 text-muted-foreground transition-transform group-hover:translate-x-1" />
          </div>
        </div>
      </div>
    </Link>
  );
}
