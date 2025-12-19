'use client';

import { useTranslations } from 'next-intl';
import { useTextbooks } from '@/lib/hooks/use-textbooks';
import { TextbookCard } from '@/components/textbooks';
import { BookOpen, Loader2, AlertCircle } from 'lucide-react';

export default function SubjectsPage() {
  const t = useTranslations('home');
  const tCommon = useTranslations('common');
  const tTextbook = useTranslations('textbook');
  const { data: textbooks, isLoading, error, refetch } = useTextbooks();

  // Loading State
  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-6 md:py-8">
        <h1 className="mb-6 text-2xl font-bold text-foreground">{t('subjects.title')}</h1>
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="ml-2 text-muted-foreground">{tCommon('loading')}</span>
        </div>
      </div>
    );
  }

  // Error State
  if (error) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-6 md:py-8">
        <h1 className="mb-6 text-2xl font-bold text-foreground">{t('subjects.title')}</h1>
        <div className="card-flat p-6 text-center">
          <AlertCircle className="mx-auto h-10 w-10 text-destructive" />
          <p className="mt-2 text-sm text-muted-foreground">{tTextbook('errorLoading')}</p>
          <button
            onClick={() => refetch()}
            className="mt-4 rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
          >
            {tCommon('retry')}
          </button>
        </div>
      </div>
    );
  }

  // Empty State
  if (!textbooks || textbooks.length === 0) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-6 md:py-8">
        <h1 className="mb-6 text-2xl font-bold text-foreground">{t('subjects.title')}</h1>
        <div className="card-flat p-8 text-center">
          <BookOpen className="mx-auto h-12 w-12 text-muted-foreground/50" />
          <p className="mt-4 text-muted-foreground">{tTextbook('noTextbooks')}</p>
        </div>
      </div>
    );
  }

  // Success State
  return (
    <div className="mx-auto max-w-7xl px-4 py-6 md:py-8">
      <h1 className="mb-6 text-2xl font-bold text-foreground">{t('subjects.title')}</h1>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {textbooks.map((textbook) => (
          <TextbookCard key={textbook.id} textbook={textbook} />
        ))}
      </div>
    </div>
  );
}
