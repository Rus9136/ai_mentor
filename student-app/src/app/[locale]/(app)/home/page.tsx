'use client';

import { useTranslations } from 'next-intl';
import { useAuth } from '@/providers/auth-provider';
import { useTextbooks } from '@/lib/hooks/use-textbooks';
import { useStudentStats, useStudentProfile } from '@/lib/hooks/use-profile';
import { Link } from '@/i18n/routing';
import { TextbookCard } from '@/components/textbooks';
import { ReviewCard } from '@/components/reviews/ReviewCard';
import { MyQuizzesWidget } from '@/components/quiz/MyQuizzesWidget';
import {
  BookOpen,
  Play,
  Flame,
  CheckCircle2,
  ChevronRight,
  ClipboardList,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { XpLevelWidget } from '@/components/gamification/XpLevelWidget';

export default function HomePage() {
  const t = useTranslations('home');
  const tCommon = useTranslations('common');
  const { user } = useAuth();
  const { data: textbooks, isLoading, error } = useTextbooks();
  const { data: stats } = useStudentStats();
  const { data: profile } = useStudentProfile();

  // Filter to only show textbooks matching student's grade
  const myTextbooks = textbooks?.filter(
    (tb) => profile?.grade_level && tb.grade_level === profile.grade_level
  ) ?? textbooks;

  const greeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return t('greeting.morning');
    if (hour < 18) return t('greeting.afternoon');
    return t('greeting.evening');
  };

  // Find the textbook with most recent activity for "Continue Learning"
  const continueItem = myTextbooks?.find((tb) => tb.last_activity && tb.progress.percentage > 0);

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 md:py-8">
      {/* Greeting Section */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-foreground md:text-3xl">
          {greeting()}, {user?.first_name}! 👋
        </h1>
        <p className="mt-1 text-muted-foreground">{t('subtitle')}</p>
      </div>

      {/* XP Level Widget */}
      <XpLevelWidget />

      {/* Continue Learning Card */}
      {continueItem && (
        <div className="mb-8">
          <Link href={`/subjects/${continueItem.id}`}>
            <div className="group card-elevated overflow-hidden p-0 transition-all hover:shadow-soft-lg">
              <div className="flex items-stretch">
                {/* Left accent */}
                <div className="w-2 bg-primary" />

                <div className="flex flex-1 items-center justify-between p-4 md:p-6">
                  <div className="flex-1">
                    <div className="mb-1 flex items-center gap-2">
                      <Play className="h-4 w-4 text-primary" />
                      <span className="text-sm font-semibold text-primary">
                        {t('continue.label')}
                      </span>
                    </div>
                    <h3 className="text-lg font-bold text-foreground">
                      {continueItem.title}
                    </h3>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {continueItem.subject} • {continueItem.progress.chapters_completed} / {continueItem.progress.chapters_total} {t('subjects.chapters')}
                    </p>

                    {/* Progress bar */}
                    <div className="mt-3 flex items-center gap-3">
                      <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full rounded-full bg-primary transition-all"
                          style={{ width: `${continueItem.progress.percentage}%` }}
                        />
                      </div>
                      <span className="text-xs font-medium text-muted-foreground">
                        {continueItem.progress.percentage}%
                      </span>
                    </div>
                  </div>

                  <ChevronRight className="ml-4 h-6 w-6 text-muted-foreground transition-transform group-hover:translate-x-1" />
                </div>
              </div>
            </div>
          </Link>
        </div>
      )}

      {/* My Quizzes Widget */}
      <MyQuizzesWidget />

      {/* Spaced Repetition — Reviews Due Today */}
      <ReviewCard />

      {/* Stats Row */}
      <div className="mb-8 grid grid-cols-3 gap-3 md:gap-4">
        <div className="card-flat p-4 text-center">
          <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-orange-100">
            <Flame className="h-5 w-5 text-orange-500" />
          </div>
          <p className="text-2xl font-bold text-foreground">{stats?.streak_days ?? 0}</p>
          <p className="text-xs text-muted-foreground">{t('stats.streak')}</p>
        </div>
        <div className="card-flat p-4 text-center">
          <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-green-100">
            <CheckCircle2 className="h-5 w-5 text-green-500" />
          </div>
          <p className="text-2xl font-bold text-foreground">
            {stats?.total_paragraphs_completed ?? 0}
          </p>
          <p className="text-xs text-muted-foreground">{t('stats.paragraphs')}</p>
        </div>
        <div className="card-flat p-4 text-center">
          <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-blue-100">
            <ClipboardList className="h-5 w-5 text-blue-500" />
          </div>
          <p className="text-2xl font-bold text-foreground">{stats?.total_tasks_completed ?? 0}</p>
          <p className="text-xs text-muted-foreground">{t('stats.tasks')}</p>
        </div>
      </div>

      {/* Subjects Section */}
      <div>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-bold text-foreground">{t('subjects.title')}</h2>
          <Link
            href="/subjects"
            className="flex items-center gap-1 text-sm font-medium text-primary hover:underline"
          >
            {t('subjects.viewAll')}
            <ChevronRight className="h-4 w-4" />
          </Link>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <span className="ml-2 text-muted-foreground">{tCommon('loading')}</span>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="card-flat p-6 text-center">
            <AlertCircle className="mx-auto h-10 w-10 text-destructive" />
            <p className="mt-2 text-sm text-muted-foreground">{tCommon('error')}</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
            >
              {tCommon('retry')}
            </button>
          </div>
        )}

        {/* Textbooks Grid */}
        {!isLoading && !error && myTextbooks && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {myTextbooks.length === 0 ? (
              <div className="col-span-full card-flat p-8 text-center">
                <BookOpen className="mx-auto h-12 w-12 text-muted-foreground/50" />
                <p className="mt-4 text-muted-foreground">
                  Учебники пока не доступны
                </p>
              </div>
            ) : (
              myTextbooks.map((textbook) => (
                <TextbookCard key={textbook.id} textbook={textbook} />
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
