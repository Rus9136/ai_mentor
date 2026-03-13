'use client';

import { Flame } from 'lucide-react';

interface StreakBadgeProps {
  days: number;
  isActive?: boolean;
}

export function StreakBadge({ days, isActive = false }: StreakBadgeProps) {
  return (
    <div
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-sm font-semibold ${
        isActive
          ? 'bg-orange-100 text-orange-600'
          : 'bg-muted text-muted-foreground'
      }`}
    >
      <Flame className={`h-4 w-4 ${isActive ? 'text-orange-500' : ''}`} />
      <span>{days}</span>
    </div>
  );
}
