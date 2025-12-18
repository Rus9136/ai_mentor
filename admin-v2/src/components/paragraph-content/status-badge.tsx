'use client';

import { Badge } from '@/components/ui/badge';
import type { ContentStatus } from '@/types';
import { Circle, CheckCircle2, AlertCircle, Clock } from 'lucide-react';

interface StatusBadgeProps {
  status: ContentStatus;
  className?: string;
}

const statusConfig: Record<
  ContentStatus,
  { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: typeof Circle }
> = {
  empty: {
    label: 'Пусто',
    variant: 'outline',
    icon: Circle,
  },
  draft: {
    label: 'Черновик',
    variant: 'secondary',
    icon: Clock,
  },
  ready: {
    label: 'Готово',
    variant: 'default',
    icon: CheckCircle2,
  },
  outdated: {
    label: 'Устарело',
    variant: 'destructive',
    icon: AlertCircle,
  },
};

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <Badge variant={config.variant} className={className}>
      <Icon className="h-3 w-3 mr-1" />
      {config.label}
    </Badge>
  );
}
