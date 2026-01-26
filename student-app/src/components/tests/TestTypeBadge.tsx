'use client';

import { useTranslations } from 'next-intl';
import { TestPurpose } from '@/lib/api/tests';
import { cn } from '@/lib/utils';

interface TestTypeBadgeProps {
  type: TestPurpose;
  className?: string;
}

const typeStyles: Record<TestPurpose, string> = {
  diagnostic: 'bg-blue-100 text-blue-700 border-blue-200',
  formative: 'bg-green-100 text-green-700 border-green-200',
  summative: 'bg-purple-100 text-purple-700 border-purple-200',
  practice: 'bg-amber-100 text-amber-700 border-amber-200',
};

export function TestTypeBadge({ type, className }: TestTypeBadgeProps) {
  const t = useTranslations('tests.type');

  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border',
        typeStyles[type],
        className
      )}
    >
      {t(type)}
    </span>
  );
}
