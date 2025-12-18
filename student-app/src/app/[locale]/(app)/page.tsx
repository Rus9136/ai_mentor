'use client';

import { useTranslations } from 'next-intl';
import { useAuth } from '@/providers/auth-provider';
import { useTextbooks } from '@/lib/hooks/use-textbooks';
import { Link } from '@/i18n/routing';
import {
  BookOpen,
  Play,
  Flame,
  CheckCircle2,
  ChevronRight,
  TrendingUp,
  Trophy,
  Loader2,
  AlertCircle,
} from 'lucide-react';

// Subject icons mapping
const SUBJECT_ICONS: Record<string, string> = {
  'история': '📜',
  'история казахстана': '📜',
  'всемирная история': '📜',
  'алгебра': '📐',
  'математика': '📐',
  'геометрия': '📐',
  'физика': '⚡',
  'биология': '🧬',
  'химия': '🧪',
  'география': '🌍',
  'информатика': '💻',
  'английский': '🇬🇧',
  'казахский': '🇰🇿',
  'русский': '📝',
  'литература': '📚',
};

// Subject colors mapping
const SUBJECT_COLORS: Record<string, string> = {
  'история': 'bg-amber-500',
  'история казахстана': 'bg-amber-500',
  'всемирная история': 'bg-amber-600',
  'алгебра': 'bg-blue-500',
  'математика': 'bg-blue-500',
  'геометрия': 'bg-blue-600',
  'физика': 'bg-purple-500',
  'биология': 'bg-green-500',
  'химия': 'bg-red-500',
  'география': 'bg-teal-500',
  'информатика': 'bg-indigo-500',
  'английский': 'bg-pink-500',
  'казахский': 'bg-cyan-500',
  'русский': 'bg-orange-500',
  'литература': 'bg-rose-500',
};

function getSubjectIcon(subject: string): string {
  const key = subject.toLowerCase();
  for (const [keyword, icon] of Object.entries(SUBJECT_ICONS)) {
    if (key.includes(keyword)) return icon;
  }
  return '📚';
}

function getSubjectColor(subject: string): string {
  const key = subject.toLowerCase();
  for (const [keyword, color] of Object.entries(SUBJECT_COLORS)) {
    if (key.includes(keyword)) return color;
  }
  return 'bg-gray-500';
}

// Mock stats - will be replaced with real API
const mockStats = {
  streakDays: 5,
  paragraphsCompleted: 12,
  questionsAnswered: 48,
};

export default function HomePage() {
  const t = useTranslations('home');
  const tCommon = useTranslations('common');
  const { user } = useAuth();
  const { data: textbooks, isLoading, error } = useTextbooks();

  const greeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return t('greeting.morning');
    if (hour < 18) return t('greeting.afternoon');
    return t('greeting.evening');
  };

  // Find the textbook with most recent activity for "Continue Learning"
  const continueItem = textbooks?.find((tb) => tb.last_activity && tb.progress.percentage > 0);

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 md:py-8">
      {/* Greeting Section */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-foreground md:text-3xl">
          {greeting()}, {user?.first_name}! 👋
        </h1>
        <p className="mt-1 text-muted-foreground">{t('subtitle')}</p>
      </div>

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

      {/* Stats Row */}
      <div className="mb-8 grid grid-cols-3 gap-3 md:gap-4">
        <div className="card-flat p-4 text-center">
          <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-orange-100">
            <Flame className="h-5 w-5 text-orange-500" />
          </div>
          <p className="text-2xl font-bold text-foreground">{mockStats.streakDays}</p>
          <p className="text-xs text-muted-foreground">{t('stats.streak')}</p>
        </div>
        <div className="card-flat p-4 text-center">
          <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-green-100">
            <CheckCircle2 className="h-5 w-5 text-green-500" />
          </div>
          <p className="text-2xl font-bold text-foreground">
            {textbooks?.reduce((sum, tb) => sum + tb.progress.paragraphs_completed, 0) || mockStats.paragraphsCompleted}
          </p>
          <p className="text-xs text-muted-foreground">{t('stats.paragraphs')}</p>
        </div>
        <div className="card-flat p-4 text-center">
          <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-blue-100">
            <Trophy className="h-5 w-5 text-blue-500" />
          </div>
          <p className="text-2xl font-bold text-foreground">{mockStats.questionsAnswered}</p>
          <p className="text-xs text-muted-foreground">{t('stats.questions')}</p>
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
        {!isLoading && !error && textbooks && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {textbooks.length === 0 ? (
              <div className="col-span-full card-flat p-8 text-center">
                <BookOpen className="mx-auto h-12 w-12 text-muted-foreground/50" />
                <p className="mt-4 text-muted-foreground">
                  Учебники пока не доступны
                </p>
              </div>
            ) : (
              textbooks.map((textbook) => (
                <Link key={textbook.id} href={`/subjects/${textbook.id}`}>
                  <div className="card-elevated group h-full overflow-hidden transition-all hover:shadow-soft-lg">
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
                        {textbook.progress.chapters_completed} / {textbook.progress.chapters_total} {t('subjects.chapters')}
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
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
