'use client';

import { useTranslations } from 'next-intl';
import { DifficultyLevel } from '@/lib/api/tests';
import { cn } from '@/lib/utils';

interface DifficultyBadgeProps {
  difficulty: DifficultyLevel;
  className?: string;
}

const difficultyStyles: Record<DifficultyLevel, string> = {
  easy: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  medium: 'bg-orange-100 text-orange-700 border-orange-200',
  hard: 'bg-red-100 text-red-700 border-red-200',
};

export function DifficultyBadge({ difficulty, className }: DifficultyBadgeProps) {
  const t = useTranslations('tests.difficulty');

  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border',
        difficultyStyles[difficulty],
        className
      )}
    >
      {t(difficulty)}
    </span>
  );
}
