'use client';

import { useTranslations } from 'next-intl';
import { StudentHomeworkStatus } from '@/lib/api/homework';
import { cn } from '@/lib/utils';

interface HomeworkStatusBadgeProps {
  status: StudentHomeworkStatus;
  isOverdue?: boolean;
  className?: string;
}

const statusStyles: Record<StudentHomeworkStatus, string> = {
  [StudentHomeworkStatus.ASSIGNED]:
    'bg-blue-100 text-blue-700 border-blue-200',
  [StudentHomeworkStatus.IN_PROGRESS]:
    'bg-amber-100 text-amber-700 border-amber-200',
  [StudentHomeworkStatus.SUBMITTED]:
    'bg-green-100 text-green-700 border-green-200',
  [StudentHomeworkStatus.GRADED]:
    'bg-purple-100 text-purple-700 border-purple-200',
  [StudentHomeworkStatus.RETURNED]:
    'bg-orange-100 text-orange-700 border-orange-200',
};

export function HomeworkStatusBadge({
  status,
  isOverdue,
  className,
}: HomeworkStatusBadgeProps) {
  const t = useTranslations('homework.status');

  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border',
        statusStyles[status],
        isOverdue && 'ring-2 ring-red-400 ring-offset-1',
        className
      )}
    >
      {t(status)}
    </span>
  );
}
