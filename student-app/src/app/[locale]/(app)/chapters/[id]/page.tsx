'use client';

import { use, useMemo } from 'react';
import { useTranslations } from 'next-intl';
import { Link, useRouter } from '@/i18n/routing';
import { useChapterParagraphs, useParagraphNavigation } from '@/lib/hooks/use-textbooks';
import {
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  Clock,
  Loader2,
  AlertCircle,
  PlayCircle,
  FileText,
  Trophy,
} from 'lucide-react';

// Paragraph status config
const STATUS_CONFIG = {
  completed: {
    icon: CheckCircle2,
    color: 'text-success',
    bgColor: 'bg-success/10',
    borderColor: 'border-success/20',
  },
  in_progress: {
    icon: PlayCircle,
    color: 'text-primary',
    bgColor: 'bg-primary/10',
    borderColor: 'border-primary/20',
  },
  not_started: {
    icon: FileText,
    color: 'text-muted-foreground',
    bgColor: 'bg-muted',
    borderColor: 'border-border',
  },
};

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function ChapterPage({ params }: PageProps) {
  const { id } = use(params);
  const chapterId = parseInt(id, 10);

  const t = useTranslations('chapter');
  const tCommon = useTranslations('common');
  const router = useRouter();

  // Get paragraphs for this chapter
  const { data: paragraphs, isLoading, error } = useChapterParagraphs(chapterId);

  // Get chapter info from first paragraph's navigation (if available)
  const firstParagraphId = paragraphs?.[0]?.id;
  const { data: navigation } = useParagraphNavigation(firstParagraphId);

  // Calculate chapter progress
  const progress = useMemo(() => {
    if (!paragraphs || paragraphs.length === 0) {
      return { total: 0, completed: 0, percentage: 0 };
    }
    const total = paragraphs.length;
    const completed = paragraphs.filter((p) => p.status === 'completed').length;
    const percentage = Math.round((completed / total) * 100);
    return { total, completed, percentage };
  }, [paragraphs]);

  // Find current paragraph (first not completed, or last one)
  const currentParagraph = useMemo(() => {
    if (!paragraphs || paragraphs.length === 0) return null;
    return (
      paragraphs.find((p) => p.status === 'in_progress') ||
      paragraphs.find((p) => p.status === 'not_started') ||
      paragraphs[paragraphs.length - 1]
    );
  }, [paragraphs]);

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <span className="ml-2 text-muted-foreground">{tCommon('loading')}</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-12 text-center">
        <AlertCircle className="mx-auto h-12 w-12 text-destructive" />
        <h2 className="mt-4 text-lg font-bold">{tCommon('error')}</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          {t('errorLoading')}
        </p>
        <button
          onClick={() => router.back()}
          className="mt-6 rounded-full bg-primary px-6 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
        >
          {tCommon('back')}
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-6">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => router.back()}
          className="mb-4 flex items-center gap-1 text-sm font-medium text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          {tCommon('back')}
        </button>

        <div>
          {/* Breadcrumb */}
          {navigation && (
            <p className="mb-1 text-sm text-muted-foreground">
              <Link href={`/subjects/${navigation.textbook_id}`} className="hover:text-primary">
                {navigation.textbook_title}
              </Link>
            </p>
          )}

          <h1 className="text-2xl font-bold text-foreground md:text-3xl">
            {navigation ? (
              <>
                {t('chapterNumber', { number: navigation.chapter_number })}. {navigation.chapter_title}
              </>
            ) : (
              t('chapter')
            )}
          </h1>
        </div>

        {/* Progress Card */}
        <div className="mt-4 card-flat p-4">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">{t('progress')}</span>
            <span className="font-semibold text-foreground">{progress.percentage}%</span>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary transition-all"
              style={{ width: `${progress.percentage}%` }}
            />
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            {progress.completed} / {progress.total} {t('paragraphsCompleted')}
          </p>
        </div>

        {/* Continue Button */}
        {currentParagraph && progress.percentage < 100 && (
          <Link href={`/paragraphs/${currentParagraph.id}`}>
            <div className="mt-4 card-elevated group flex items-center justify-between p-4 transition-all hover:shadow-soft-lg">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                  <PlayCircle className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="font-semibold text-foreground">
                    {currentParagraph.status === 'in_progress' ? t('continue') : t('start')}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    §{currentParagraph.number} {currentParagraph.title}
                  </p>
                </div>
              </div>
              <ChevronRight className="h-5 w-5 text-muted-foreground transition-transform group-hover:translate-x-1" />
            </div>
          </Link>
        )}
      </div>

      {/* Paragraphs List */}
      <div>
        <h2 className="mb-4 text-lg font-bold text-foreground">{t('paragraphs')}</h2>

        {paragraphs && paragraphs.length === 0 ? (
          <div className="card-flat p-8 text-center">
            <BookOpen className="mx-auto h-12 w-12 text-muted-foreground/50" />
            <p className="mt-4 text-muted-foreground">{t('noParagraphs')}</p>
          </div>
        ) : (
          <div className="space-y-3">
            {paragraphs?.map((paragraph) => {
              const StatusIcon = STATUS_CONFIG[paragraph.status].icon;

              return (
                <Link key={paragraph.id} href={`/paragraphs/${paragraph.id}`}>
                  <div
                    className={`card-flat group overflow-hidden border transition-all hover:shadow-soft hover:border-primary/30 ${
                      STATUS_CONFIG[paragraph.status].borderColor
                    }`}
                  >
                    <div className="flex items-center gap-4 p-4">
                      {/* Status Icon */}
                      <div
                        className={`flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl ${
                          STATUS_CONFIG[paragraph.status].bgColor
                        }`}
                      >
                        {paragraph.status === 'completed' ? (
                          <StatusIcon className={`h-5 w-5 ${STATUS_CONFIG[paragraph.status].color}`} />
                        ) : (
                          <span className={`text-sm font-bold ${STATUS_CONFIG[paragraph.status].color}`}>
                            §{paragraph.number}
                          </span>
                        )}
                      </div>

                      {/* Paragraph Info */}
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-foreground group-hover:text-primary truncate">
                          {paragraph.title || `§${paragraph.number}`}
                        </h3>

                        <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
                          {/* Estimated Time */}
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {paragraph.estimated_time} {t('minutes')}
                          </span>

                          {/* Status */}
                          <span className="flex items-center gap-1">
                            <StatusIcon className={`h-3 w-3 ${STATUS_CONFIG[paragraph.status].color}`} />
                            {t(`status.${paragraph.status}`)}
                          </span>

                          {/* Practice indicator */}
                          {paragraph.has_practice && (
                            <span className="flex items-center gap-1">
                              <Trophy className={`h-3 w-3 ${paragraph.practice_score ? 'text-success' : 'text-muted-foreground'}`} />
                              {paragraph.practice_score
                                ? `${Math.round(paragraph.practice_score * 100)}%`
                                : t('hasPractice')
                              }
                            </span>
                          )}
                        </div>

                        {/* Summary preview */}
                        {paragraph.summary && (
                          <p className="mt-1 text-xs text-muted-foreground line-clamp-1">
                            {paragraph.summary}
                          </p>
                        )}
                      </div>

                      {/* Arrow */}
                      <ChevronRight className="h-5 w-5 flex-shrink-0 text-muted-foreground transition-transform group-hover:translate-x-1" />
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
