'use client';

import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { AlertTriangle, Lock, ChevronRight } from 'lucide-react';
import { PrerequisiteWarning as PrerequisiteWarningType } from '@/lib/api/prerequisites';

interface PrerequisiteWarningProps {
  warnings: PrerequisiteWarningType[];
  canProceed: boolean;
  onProceedAnyway?: () => void;
}

export function PrerequisiteWarning({ warnings, canProceed, onProceedAnyway }: PrerequisiteWarningProps) {
  const t = useTranslations('prerequisites');

  const requiredWarnings = warnings.filter(w => w.strength === 'required');
  const recommendedWarnings = warnings.filter(w => w.strength === 'recommended');

  return (
    <div className={`rounded-xl border p-4 mb-6 ${
      !canProceed
        ? 'border-destructive/30 bg-destructive/5'
        : 'border-amber-300 bg-amber-50 dark:border-amber-500/30 dark:bg-amber-500/5'
    }`}>
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        {!canProceed ? (
          <Lock className="h-5 w-5 text-destructive flex-shrink-0" />
        ) : (
          <AlertTriangle className="h-5 w-5 text-amber-500 flex-shrink-0" />
        )}
        <h3 className="font-semibold text-foreground">
          {!canProceed ? t('requiredTitle') : t('recommendedTitle')}
        </h3>
      </div>

      {/* Required prerequisites */}
      {requiredWarnings.length > 0 && (
        <div className="space-y-2 mb-3">
          {requiredWarnings.map((warning) => (
            <PrerequisiteItem key={warning.paragraph_id} warning={warning} />
          ))}
        </div>
      )}

      {/* Recommended prerequisites */}
      {recommendedWarnings.length > 0 && (
        <div className="space-y-2 mb-3">
          {recommendedWarnings.map((warning) => (
            <PrerequisiteItem key={warning.paragraph_id} warning={warning} />
          ))}
        </div>
      )}

      {/* Action buttons */}
      {!canProceed && onProceedAnyway && (
        <div className="mt-4 flex items-center gap-3">
          {requiredWarnings.length > 0 && (
            <Link
              href={`/paragraphs/${requiredWarnings[0].paragraph_id}`}
              className="flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 transition-all"
            >
              {t('goToPrerequisite')}
              <ChevronRight className="h-4 w-4" />
            </Link>
          )}
          <button
            onClick={onProceedAnyway}
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            {t('proceedAnyway')}
          </button>
        </div>
      )}
    </div>
  );
}

function PrerequisiteItem({ warning }: { warning: PrerequisiteWarningType }) {
  const t = useTranslations('prerequisites');
  const scorePercent = Math.round(warning.current_score * 100);
  const isRequired = warning.strength === 'required';

  return (
    <Link
      href={`/paragraphs/${warning.paragraph_id}`}
      className="flex items-center gap-3 rounded-lg bg-background/80 p-3 hover:bg-background transition-colors group"
    >
      <div className={`h-2 w-2 rounded-full flex-shrink-0 ${isRequired ? 'bg-destructive' : 'bg-amber-400'}`} />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-foreground truncate group-hover:text-primary">
          {warning.paragraph_number != null && `§${warning.paragraph_number}. `}
          {warning.paragraph_title || t('untitled')}
        </p>
        <p className="text-xs text-muted-foreground">
          {warning.textbook_title && (
            <span>{warning.textbook_title}{warning.grade_level ? ` (${warning.grade_level} ${t('grade')})` : ''} — </span>
          )}
          {t('yourLevel')}: {scorePercent}% — {t('needed')}: 60%+
        </p>
      </div>
      <ChevronRight className="h-4 w-4 text-muted-foreground flex-shrink-0 group-hover:translate-x-0.5 transition-transform" />
    </Link>
  );
}
