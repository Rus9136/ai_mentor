'use client';

import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { RefreshCw, ChevronRight, Clock } from 'lucide-react';
import { useDueReviews } from '@/lib/hooks/use-reviews';

/**
 * ReviewCard — section on the home page showing due reviews.
 * Only renders if there are reviews due today.
 */
export function ReviewCard() {
  const t = useTranslations('reviews');
  const { data, isLoading } = useDueReviews();

  if (isLoading || !data || data.due_today_count === 0) {
    return null;
  }

  return (
    <div className="mb-8">
      <div className="card-elevated overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 pb-3">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-amber-100">
              <RefreshCw className="h-4 w-4 text-amber-600" />
            </div>
            <div>
              <h3 className="font-semibold text-foreground">
                {t('title', { count: data.due_today_count })}
              </h3>
              {data.upcoming_week_count > 0 && (
                <p className="text-xs text-muted-foreground">
                  {t('weekCount', { count: data.upcoming_week_count })}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Review items list */}
        <div className="divide-y divide-border px-4">
          {data.due_today.slice(0, 5).map((item) => (
            <Link
              key={item.id}
              href={`/paragraphs/${item.paragraph_id}`}
              className="flex items-center gap-3 py-3 group"
            >
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground truncate group-hover:text-primary">
                  {item.paragraph_number && `§${item.paragraph_number}. `}
                  {item.paragraph_title || t('untitled')}
                </p>
                <p className="text-xs text-muted-foreground truncate">
                  {item.textbook_title}
                  {item.chapter_title && ` — ${item.chapter_title}`}
                </p>
              </div>

              {/* Streak indicator */}
              <div className="flex items-center gap-2 flex-shrink-0">
                <div className="flex gap-0.5">
                  {Array.from({ length: 7 }).map((_, i) => (
                    <div
                      key={i}
                      className={`h-1.5 w-1.5 rounded-full ${
                        i < item.streak ? 'bg-success' : 'bg-muted'
                      }`}
                    />
                  ))}
                </div>
                <Clock className="h-3 w-3 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">2 {t('minutes')}</span>
              </div>

              <ChevronRight className="h-4 w-4 text-muted-foreground flex-shrink-0 group-hover:translate-x-0.5 transition-transform" />
            </Link>
          ))}
        </div>

        {/* Show more if > 5 */}
        {data.due_today_count > 5 && (
          <div className="px-4 py-3 border-t border-border">
            <p className="text-xs text-muted-foreground text-center">
              {t('moreReviews', { count: data.due_today_count - 5 })}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
