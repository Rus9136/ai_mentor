'use client';

import { useTranslations } from 'next-intl';
import { Badge } from '@/components/ui/badge';
import { HomeworkStatus } from '@/types/homework';

interface HomeworkStatusBadgeProps {
  status: HomeworkStatus;
  className?: string;
}

export function HomeworkStatusBadge({ status, className }: HomeworkStatusBadgeProps) {
  const t = useTranslations('homework.status');

  const variants: Record<HomeworkStatus, 'default' | 'secondary' | 'success' | 'warning' | 'destructive'> = {
    [HomeworkStatus.DRAFT]: 'secondary',
    [HomeworkStatus.PUBLISHED]: 'success',
    [HomeworkStatus.CLOSED]: 'destructive',
    [HomeworkStatus.ARCHIVED]: 'default',
  };

  return (
    <Badge variant={variants[status]} className={className}>
      {t(status)}
    </Badge>
  );
}
