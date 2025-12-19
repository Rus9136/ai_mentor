'use client';

import { useTranslations } from 'next-intl';
import { Flame, BookOpen, CheckCircle2, Clock } from 'lucide-react';
import { StudentStats } from '@/lib/api/profile';

interface StatsCardsProps {
  stats: StudentStats | undefined;
  isLoading: boolean;
}

export function StatsCards({ stats, isLoading }: StatsCardsProps) {
  const t = useTranslations('profile');

  // Format time: convert minutes to hours and minutes
  const formatTime = (minutes: number) => {
    if (minutes < 60) {
      return { value: minutes, unit: t('stats.time') };
    }
    const hours = Math.floor(minutes / 60);
    return { value: hours, unit: t('stats.hours') };
  };

  const timeDisplay = formatTime(stats?.total_time_spent_minutes ?? 0);

  const cards = [
    {
      icon: Flame,
      value: stats?.streak_days ?? 0,
      label: t('stats.streak'),
      title: t('stats.streakTitle'),
      bgColor: 'bg-orange-100',
      iconColor: 'text-orange-500',
    },
    {
      icon: BookOpen,
      value: stats?.total_paragraphs_completed ?? 0,
      label: t('stats.paragraphs'),
      title: t('stats.paragraphsTitle'),
      bgColor: 'bg-green-100',
      iconColor: 'text-green-600',
    },
    {
      icon: CheckCircle2,
      value: stats?.total_tasks_completed ?? 0,
      label: t('stats.tasks'),
      title: t('stats.tasksTitle'),
      bgColor: 'bg-blue-100',
      iconColor: 'text-blue-500',
    },
    {
      icon: Clock,
      value: timeDisplay.value,
      label: timeDisplay.unit,
      title: t('stats.timeTitle'),
      bgColor: 'bg-purple-100',
      iconColor: 'text-purple-500',
    },
  ];

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4 md:gap-4">
        {cards.map((_, i) => (
          <div key={i} className="card-flat animate-pulse p-4 text-center">
            <div className="mx-auto mb-2 h-10 w-10 rounded-full bg-muted" />
            <div className="mx-auto h-7 w-12 rounded bg-muted" />
            <div className="mx-auto mt-1 h-4 w-16 rounded bg-muted" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4 md:gap-4">
      {cards.map((card) => (
        <div key={card.title} className="card-flat p-4 text-center">
          <div
            className={`mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full ${card.bgColor}`}
          >
            <card.icon className={`h-5 w-5 ${card.iconColor}`} />
          </div>
          <p className="text-2xl font-bold text-foreground">{card.value}</p>
          <p className="text-xs text-muted-foreground">{card.label}</p>
        </div>
      ))}
    </div>
  );
}
