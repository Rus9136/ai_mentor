'use client';

import { useTranslations } from 'next-intl';
import { BarChart3, Settings, Loader2 } from 'lucide-react';
import { useAuth } from '@/providers/auth-provider';
import { useStudentStats, useMasteryOverview } from '@/lib/hooks/use-profile';
import {
  ProfileHeader,
  StatsCards,
  MasteryOverviewComponent,
  SettingsSection,
} from '@/components/profile';

export default function ProfilePage() {
  const t = useTranslations('profile');
  const { user, isLoading: isAuthLoading } = useAuth();

  const { data: stats, isLoading: isStatsLoading } = useStudentStats();
  const { data: masteryOverview, isLoading: isMasteryLoading } = useMasteryOverview();

  if (isAuthLoading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-6 md:py-8">
      {/* Profile Header */}
      <ProfileHeader user={user} className="mb-8" />

      {/* Stats Section */}
      <section className="mb-8">
        <div className="mb-4 flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-bold text-foreground">{t('myStats')}</h2>
        </div>
        <StatsCards stats={stats} isLoading={isStatsLoading} />
      </section>

      {/* Mastery Section */}
      <section className="mb-8">
        <div className="mb-4 flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-bold text-foreground">{t('myLevel')}</h2>
        </div>
        <div className="card-flat p-4">
          <MasteryOverviewComponent data={masteryOverview} isLoading={isMasteryLoading} />
        </div>
      </section>

      {/* Settings Section */}
      <section>
        <div className="mb-4 flex items-center gap-2">
          <Settings className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-bold text-foreground">{t('settings')}</h2>
        </div>
        <SettingsSection />
      </section>
    </div>
  );
}
