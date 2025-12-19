'use client';

import { Link } from '@/i18n/routing';
import { TrendingUp } from 'lucide-react';
import { useTranslations } from 'next-intl';
import { StudentTextbook } from '@/lib/api/textbooks';
import { getSubjectIcon, getSubjectColor } from './subject-utils';

interface TextbookCardProps {
  textbook: StudentTextbook;
  className?: string;
}

export function TextbookCard({ textbook, className = '' }: TextbookCardProps) {
  const t = useTranslations('home');

  return (
    <Link href={`/subjects/${textbook.id}`}>
      <div
        className={`card-elevated group h-full overflow-hidden transition-all hover:shadow-soft-lg ${className}`}
      >
        {/* Subject Icon & Title */}
        <div className="p-4">
          <div className="mb-3 flex items-start justify-between">
            <div
              className={`flex h-12 w-12 items-center justify-center rounded-2xl ${getSubjectColor(textbook.subject)} text-2xl`}
            >
              {getSubjectIcon(textbook.subject)}
            </div>
            <div className="flex items-center gap-2">
              {textbook.mastery_level && (
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-bold ${
                    textbook.mastery_level === 'A'
                      ? 'bg-green-100 text-green-700'
                      : textbook.mastery_level === 'B'
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-orange-100 text-orange-700'
                  }`}
                >
                  {textbook.mastery_level}
                </span>
              )}
              {textbook.progress.percentage > 0 && (
                <div className="flex items-center gap-1 text-xs font-medium text-success">
                  <TrendingUp className="h-3 w-3" />
                  {textbook.progress.percentage}%
                </div>
              )}
            </div>
          </div>

          <h3 className="font-bold text-foreground group-hover:text-primary">
            {textbook.title}
          </h3>

          <p className="mt-1 text-sm text-muted-foreground">
            {textbook.progress.chapters_completed} / {textbook.progress.chapters_total}{' '}
            {t('subjects.chapters')}
          </p>
        </div>

        {/* Progress Bar */}
        <div className="h-1.5 bg-muted">
          <div
            className={`h-full ${getSubjectColor(textbook.subject)} transition-all`}
            style={{ width: `${textbook.progress.percentage}%` }}
          />
        </div>
      </div>
    </Link>
  );
}
