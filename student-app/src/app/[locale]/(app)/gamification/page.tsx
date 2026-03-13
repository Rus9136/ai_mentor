'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { useGamificationProfile } from '@/lib/hooks/use-gamification';
import { XpProgressBar } from '@/components/gamification/XpProgressBar';
import { StreakBadge } from '@/components/gamification/StreakBadge';
import { AchievementGrid } from '@/components/gamification/AchievementGrid';
import { Leaderboard } from '@/components/gamification/Leaderboard';
import { DailyQuests } from '@/components/gamification/DailyQuests';
import { Star, Flame, Trophy, Loader2 } from 'lucide-react';

type Tab = 'profile' | 'achievements' | 'leaderboard' | 'quests';

export default function GamificationPage() {
  const t = useTranslations('gamification');
  const [activeTab, setActiveTab] = useState<Tab>('profile');
  const { data: profile, isLoading } = useGamificationProfile();

  const tabs: { key: Tab; label: string }[] = [
    { key: 'profile', label: t('profile') },
    { key: 'achievements', label: t('achievements') },
    { key: 'leaderboard', label: t('leaderboard') },
    { key: 'quests', label: t('dailyQuests') },
  ];

  return (
    <div className="mx-auto max-w-2xl px-4 py-6 md:py-8">
      <h1 className="mb-6 text-2xl font-bold text-foreground">{t('title')}</h1>

      {/* Tabs */}
      <div className="mb-6 flex gap-1 overflow-x-auto rounded-xl bg-muted p-1">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex-shrink-0 rounded-lg px-3 py-2 text-sm font-semibold transition-colors ${
              activeTab === tab.key
                ? 'bg-card text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'profile' && (
        <ProfileTab profile={profile} isLoading={isLoading} />
      )}
      {activeTab === 'achievements' && <AchievementGrid />}
      {activeTab === 'leaderboard' && <Leaderboard />}
      {activeTab === 'quests' && <DailyQuests />}
    </div>
  );
}

function ProfileTab({
  profile,
  isLoading,
}: {
  profile: ReturnType<typeof useGamificationProfile>['data'];
  isLoading: boolean;
}) {
  const t = useTranslations('gamification');

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!profile) return null;

  return (
    <div className="space-y-6">
      {/* Level + XP */}
      <div className="rounded-2xl border border-border bg-card p-6 text-center">
        <div className="mx-auto mb-3 flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-blue-500 text-white shadow-md">
          <div className="text-center">
            <Star className="mx-auto h-5 w-5" />
            <span className="text-2xl font-extrabold">{profile.level}</span>
          </div>
        </div>
        <h2 className="text-lg font-bold text-foreground">
          {t('level')} {profile.level}
        </h2>
        <p className="text-sm text-muted-foreground">
          {profile.total_xp.toLocaleString()} XP
        </p>
        <div className="mx-auto mt-4 max-w-xs">
          <XpProgressBar
            currentXp={profile.xp_in_current_level}
            xpToNext={profile.xp_to_next_level}
            level={profile.level}
            size="lg"
          />
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-3 gap-3">
        {/* Streak */}
        <div className="rounded-xl border border-border bg-card p-4 text-center">
          <Flame className="mx-auto h-6 w-6 text-orange-500" />
          <p className="mt-1 text-2xl font-bold text-foreground">{profile.current_streak}</p>
          <p className="text-xs text-muted-foreground">{t('streak', { days: '' }).trim()}</p>
        </div>
        {/* Streak Record */}
        <div className="rounded-xl border border-border bg-card p-4 text-center">
          <Flame className="mx-auto h-6 w-6 text-amber-400" />
          <p className="mt-1 text-2xl font-bold text-foreground">{profile.longest_streak}</p>
          <p className="text-xs text-muted-foreground">{t('streakRecord')}</p>
        </div>
        {/* Achievements */}
        <div className="rounded-xl border border-border bg-card p-4 text-center">
          <Trophy className="mx-auto h-6 w-6 text-violet-500" />
          <p className="mt-1 text-2xl font-bold text-foreground">{profile.badges_earned_count}</p>
          <p className="text-xs text-muted-foreground">{t('earned')}</p>
        </div>
      </div>
    </div>
  );
}
