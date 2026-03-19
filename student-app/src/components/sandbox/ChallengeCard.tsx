'use client';

import { useTranslations } from 'next-intl';
import { CheckCircle2, Circle, Minus, Star } from 'lucide-react';
import type { ChallengeListItem } from '@/lib/api/coding';
import { useRouter } from 'next/navigation';

interface ChallengeCardProps {
  challenge: ChallengeListItem;
  index: number;
}

const difficultyColors = {
  easy: 'text-green-600 bg-green-100 dark:bg-green-900/30',
  medium: 'text-amber-600 bg-amber-100 dark:bg-amber-900/30',
  hard: 'text-red-600 bg-red-100 dark:bg-red-900/30',
};

export function ChallengeCard({ challenge, index }: ChallengeCardProps) {
  const t = useTranslations('challenges');
  const router = useRouter();

  const statusIcon =
    challenge.status === 'solved' ? (
      <CheckCircle2 className="h-5 w-5 text-green-500" />
    ) : challenge.status === 'attempted' ? (
      <Minus className="h-5 w-5 text-blue-500" />
    ) : (
      <Circle className="h-5 w-5 text-muted-foreground/40" />
    );

  return (
    <button
      onClick={() => router.push(`/sandbox/challenges/${challenge.id}`)}
      className="flex items-center gap-3 w-full px-4 py-3 rounded-lg border border-border hover:bg-muted/50 transition-colors text-left"
    >
      {statusIcon}

      <span className="text-sm text-muted-foreground font-mono w-6">
        {index + 1}.
      </span>

      <span className="flex-1 text-sm font-medium truncate">
        {challenge.title}
      </span>

      <span
        className={`px-2 py-0.5 rounded text-xs font-medium ${
          difficultyColors[challenge.difficulty]
        }`}
      >
        {t(challenge.difficulty)}
      </span>

      <span className="flex items-center gap-1 text-xs text-amber-500 font-medium min-w-[50px] justify-end">
        <Star className="h-3 w-3" />
        {challenge.points}
      </span>
    </button>
  );
}
