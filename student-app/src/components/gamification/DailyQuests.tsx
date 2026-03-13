'use client';

import { useTranslations } from 'next-intl';
import { useDailyQuests } from '@/lib/hooks/use-gamification';
import { DailyQuestCard } from './DailyQuestCard';
import { Loader2, Sparkles } from 'lucide-react';

export function DailyQuests() {
  const t = useTranslations('gamification');
  const { data: quests, isLoading } = useDailyQuests();

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!quests || quests.length === 0) {
    return (
      <div className="py-12 text-center">
        <Sparkles className="mx-auto h-10 w-10 text-muted-foreground/40" />
        <p className="mt-2 text-sm text-muted-foreground">{t('noQuests')}</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {quests.map((quest) => (
        <DailyQuestCard key={quest.id} quest={quest} />
      ))}
    </div>
  );
}
