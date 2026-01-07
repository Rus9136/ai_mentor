'use client';

import { useTranslations } from 'next-intl';
import { AlertTriangle, XCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LateWarningProps {
  canSubmit: boolean;
  latePenalty?: number;
  className?: string;
}

export function LateWarning({
  canSubmit,
  latePenalty = 0,
  className,
}: LateWarningProps) {
  const t = useTranslations('homework.late');

  if (canSubmit) {
    return (
      <div
        className={cn(
          'flex items-start gap-3 p-4 rounded-xl bg-amber-50 border border-amber-200',
          className
        )}
      >
        <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <div>
          <p className="font-medium text-amber-700">{t('warning')}</p>
          {latePenalty > 0 && (
            <p className="text-sm text-amber-600 mt-1">
              {t('penaltyInfo', { percent: latePenalty })}
            </p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        'flex items-start gap-3 p-4 rounded-xl bg-red-50 border border-red-200',
        className
      )}
    >
      <XCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
      <div>
        <p className="font-medium text-red-700">{t('cannotSubmit')}</p>
        <p className="text-sm text-red-600 mt-1">{t('deadlinePassed')}</p>
      </div>
    </div>
  );
}
