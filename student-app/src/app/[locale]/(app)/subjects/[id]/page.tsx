'use client';

import { use } from 'react';
import { useTranslations } from 'next-intl';
import { Link, useRouter } from '@/i18n/routing';
import { useTextbooks, useTextbookChapters } from '@/lib/hooks/use-textbooks';
import {
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  Clock,
  Lock,
  Loader2,
  AlertCircle,
  PlayCircle,
  Trophy,
} from 'lucide-react';

// Chapter status icons and colors
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
    icon: BookOpen,
    color: 'text-muted-foreground',
    bgColor: 'bg-muted',
    borderColor: 'border-border',
  },
  locked: {
    icon: Lock,
    color: 'text-muted-foreground/50',
    bgColor: 'bg-muted/50',
    borderColor: 'border-border/50',
  },
};

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function TextbookPage({ params }: PageProps) {
  const { id } = use(params);
  const textbookId = parseInt(id, 10);

  const t = useTranslations('textbook');
  const tCommon = useTranslations('common');
  const router = useRouter();

  // Get textbook info from the list (for title, subject, etc.)
  const { data: textbooks } = useTextbooks();
  const textbook = textbooks?.find((tb) => tb.id === textbookId);

  // Get chapters
  const { data: chapters, isLoading, error } = useTextbookChapters(textbookId);

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

  // Calculate overall progress
  const totalParagraphs = chapters?.reduce((sum, ch) => sum + ch.progress.paragraphs_total, 0) || 0;
  const completedParagraphs = chapters?.reduce((sum, ch) => sum + ch.progress.paragraphs_completed, 0) || 0;
  const overallProgress = totalParagraphs > 0 ? Math.round((completedParagraphs / totalParagraphs) * 100) : 0;

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

        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-foreground md:text-3xl">
              {textbook?.title || t('untitled')}
            </h1>
            <p className="mt-1 text-muted-foreground">
              {textbook?.subject} • {textbook?.grade_level} {t('grade')}
            </p>
          </div>

          {textbook?.mastery_level && (
            <span
              className={`rounded-full px-3 py-1 text-sm font-bold ${
                textbook.mastery_level === 'A'
                  ? 'bg-success/10 text-success'
                  : textbook.mastery_level === 'B'
                    ? 'bg-primary/10 text-primary'
                    : 'bg-orange-100 text-orange-600'
              }`}
            >
              {t('level')} {textbook.mastery_level}
            </span>
          )}
        </div>

        {/* Overall Progress */}
        <div className="mt-4 card-flat p-4">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">{t('overallProgress')}</span>
            <span className="font-semibold text-foreground">{overallProgress}%</span>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary transition-all"
              style={{ width: `${overallProgress}%` }}
            />
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            {completedParagraphs} / {totalParagraphs} {t('paragraphsCompleted')}
          </p>
        </div>
      </div>

      {/* Chapters List */}
      <div>
        <h2 className="mb-4 text-lg font-bold text-foreground">{t('chapters')}</h2>

        {chapters && chapters.length === 0 ? (
          <div className="card-flat p-8 text-center">
            <BookOpen className="mx-auto h-12 w-12 text-muted-foreground/50" />
            <p className="mt-4 text-muted-foreground">{t('noChapters')}</p>
          </div>
        ) : (
          <div className="space-y-3">
            {chapters?.map((chapter, index) => {
              const StatusIcon = STATUS_CONFIG[chapter.status].icon;
              const isLocked = chapter.status === 'locked';

              const ChapterContent = (
                <div
                  className={`card-flat group overflow-hidden border transition-all ${
                    STATUS_CONFIG[chapter.status].borderColor
                  } ${!isLocked ? 'hover:shadow-soft hover:border-primary/30' : 'opacity-60'}`}
                >
                  <div className="flex items-center gap-4 p-4">
                    {/* Chapter Number & Status Icon */}
                    <div
                      className={`flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl ${
                        STATUS_CONFIG[chapter.status].bgColor
                      }`}
                    >
                      {chapter.status === 'completed' ? (
                        <StatusIcon className={`h-6 w-6 ${STATUS_CONFIG[chapter.status].color}`} />
                      ) : (
                        <span className={`text-lg font-bold ${STATUS_CONFIG[chapter.status].color}`}>
                          {chapter.number}
                        </span>
                      )}
                    </div>

                    {/* Chapter Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h3
                          className={`font-bold truncate ${
                            isLocked ? 'text-muted-foreground' : 'text-foreground group-hover:text-primary'
                          }`}
                        >
                          {chapter.title}
                        </h3>
                        {chapter.mastery_level && (
                          <span
                            className={`flex-shrink-0 rounded px-1.5 py-0.5 text-xs font-bold ${
                              chapter.mastery_level === 'A'
                                ? 'bg-success/10 text-success'
                                : chapter.mastery_level === 'B'
                                  ? 'bg-primary/10 text-primary'
                                  : 'bg-orange-100 text-orange-600'
                            }`}
                          >
                            {chapter.mastery_level}
                          </span>
                        )}
                      </div>

                      {/* Progress Bar */}
                      {!isLocked && (
                        <div className="mt-2 flex items-center gap-2">
                          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                            <div
                              className={`h-full rounded-full transition-all ${
                                chapter.status === 'completed' ? 'bg-success' : 'bg-primary'
                              }`}
                              style={{ width: `${chapter.progress.percentage}%` }}
                            />
                          </div>
                          <span className="text-xs text-muted-foreground">
                            {chapter.progress.paragraphs_completed}/{chapter.progress.paragraphs_total}
                          </span>
                        </div>
                      )}

                      {/* Status Text */}
                      <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                        {chapter.status === 'completed' && (
                          <>
                            <CheckCircle2 className="h-3 w-3 text-success" />
                            <span>{t('status.completed')}</span>
                          </>
                        )}
                        {chapter.status === 'in_progress' && (
                          <>
                            <PlayCircle className="h-3 w-3 text-primary" />
                            <span>{t('status.inProgress')}</span>
                          </>
                        )}
                        {chapter.status === 'not_started' && (
                          <span>{t('status.notStarted')}</span>
                        )}
                        {chapter.status === 'locked' && (
                          <>
                            <Lock className="h-3 w-3" />
                            <span>{t('status.locked')}</span>
                          </>
                        )}

                        {chapter.has_summative_test && (
                          <>
                            <span className="text-muted-foreground/50">•</span>
                            <Trophy className={`h-3 w-3 ${chapter.summative_passed ? 'text-success' : 'text-muted-foreground'}`} />
                            <span>{t('hasTest')}</span>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Arrow */}
                    {!isLocked && (
                      <ChevronRight className="h-5 w-5 flex-shrink-0 text-muted-foreground transition-transform group-hover:translate-x-1" />
                    )}
                  </div>
                </div>
              );

              if (isLocked) {
                return <div key={chapter.id}>{ChapterContent}</div>;
              }

              return (
                <Link key={chapter.id} href={`/chapters/${chapter.id}`}>
                  {ChapterContent}
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
