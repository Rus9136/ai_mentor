'use client';

import { useLocale, useTranslations } from 'next-intl';
import { CheckCircle2 } from 'lucide-react';
import type { DailyQuest } from '@/types/gamification';

interface DailyQuestCardProps {
  quest: DailyQuest;
}

export function DailyQuestCard({ quest }: DailyQuestCardProps) {
  const t = useTranslations('gamification');
  const locale = useLocale();

  const name = locale === 'kz' ? quest.name_kk : quest.name_ru;
  const description = locale === 'kz' ? quest.description_kk : quest.description_ru;
  const subjectName = locale === 'kz' ? quest.subject_name_kk : quest.subject_name_ru;
  const pct = quest.target_value > 0
    ? Math.min((quest.current_value / quest.target_value) * 100, 100)
    : 0;

  return (
    <div
      className={`rounded-xl border p-4 transition-all ${
        quest.is_completed
          ? 'border-emerald-200 bg-emerald-50/50'
          : 'border-border bg-card'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-foreground">{name}</p>
          {description && (
            <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>
          )}
          {subjectName && (
            <p className="mt-1 inline-block rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium text-primary">
              {subjectName}
            </p>
          )}
        </div>
        <span className={`whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-bold ${
          quest.is_completed
            ? 'bg-emerald-100 text-emerald-600'
            : 'bg-primary/10 text-primary'
        }`}>
          +{quest.xp_reward} XP
        </span>
      </div>

      <div className="mt-3">
        {quest.is_completed ? (
          <div className="flex items-center gap-1.5 text-sm font-medium text-emerald-600">
            <CheckCircle2 className="h-4 w-4" />
            <span>{t('questComplete')}</span>
          </div>
        ) : (
          <>
            <div className="h-2 overflow-hidden rounded-full bg-muted">
              <div
                className="h-2 rounded-full bg-primary transition-all duration-500"
                style={{ width: `${pct}%` }}
              />
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              {quest.current_value} / {quest.target_value}
            </p>
          </>
        )}
      </div>
    </div>
  );
}
