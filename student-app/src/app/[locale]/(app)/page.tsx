'use client';

import { useTranslations } from 'next-intl';
import { useAuth } from '@/providers/auth-provider';
import { Link } from '@/i18n/routing';
import {
  BookOpen,
  Clock,
  Play,
  Flame,
  CheckCircle2,
  ChevronRight,
  TrendingUp,
  Trophy,
} from 'lucide-react';

// Mock data - will be replaced with API calls
const mockSubjects = [
  {
    id: 1,
    title: 'История Казахстана',
    icon: '📜',
    color: 'bg-amber-500',
    progress: 35,
    chaptersTotal: 8,
    chaptersCompleted: 3,
  },
  {
    id: 2,
    title: 'Алгебра',
    icon: '📐',
    color: 'bg-blue-500',
    progress: 60,
    chaptersTotal: 10,
    chaptersCompleted: 6,
  },
  {
    id: 3,
    title: 'Физика',
    icon: '⚡',
    color: 'bg-purple-500',
    progress: 15,
    chaptersTotal: 12,
    chaptersCompleted: 2,
  },
  {
    id: 4,
    title: 'Биология',
    icon: '🧬',
    color: 'bg-green-500',
    progress: 0,
    chaptersTotal: 9,
    chaptersCompleted: 0,
  },
];

const mockContinue = {
  subjectTitle: 'История Казахстана',
  chapterTitle: 'Глава 3: Казахское ханство',
  paragraphTitle: '§3.2 Образование Казахского ханства',
  progress: 45,
};

const mockStats = {
  streakDays: 5,
  paragraphsCompleted: 12,
  questionsAnswered: 48,
};

export default function HomePage() {
  const t = useTranslations('home');
  const { user } = useAuth();

  const greeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return t('greeting.morning');
    if (hour < 18) return t('greeting.afternoon');
    return t('greeting.evening');
  };

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
      {mockContinue && (
        <div className="mb-8">
          <Link href={`/paragraphs/${1}/learn`}>
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
                      {mockContinue.paragraphTitle}
                    </h3>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {mockContinue.subjectTitle} → {mockContinue.chapterTitle}
                    </p>

                    {/* Progress bar */}
                    <div className="mt-3 flex items-center gap-3">
                      <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full rounded-full bg-primary transition-all"
                          style={{ width: `${mockContinue.progress}%` }}
                        />
                      </div>
                      <span className="text-xs font-medium text-muted-foreground">
                        {mockContinue.progress}%
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
          <p className="text-2xl font-bold text-foreground">{mockStats.paragraphsCompleted}</p>
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

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {mockSubjects.map((subject) => (
            <Link key={subject.id} href={`/subjects/${subject.id}`}>
              <div className="card-elevated group h-full overflow-hidden transition-all hover:shadow-soft-lg">
                {/* Subject Icon & Title */}
                <div className="p-4">
                  <div className="mb-3 flex items-start justify-between">
                    <div
                      className={`flex h-12 w-12 items-center justify-center rounded-2xl ${subject.color} text-2xl`}
                    >
                      {subject.icon}
                    </div>
                    {subject.progress > 0 && (
                      <div className="flex items-center gap-1 text-xs font-medium text-success">
                        <TrendingUp className="h-3 w-3" />
                        {subject.progress}%
                      </div>
                    )}
                  </div>

                  <h3 className="font-bold text-foreground group-hover:text-primary">
                    {subject.title}
                  </h3>

                  <p className="mt-1 text-sm text-muted-foreground">
                    {subject.chaptersCompleted} / {subject.chaptersTotal} {t('subjects.chapters')}
                  </p>
                </div>

                {/* Progress Bar */}
                <div className="h-1.5 bg-muted">
                  <div
                    className={`h-full ${subject.color} transition-all`}
                    style={{ width: `${subject.progress}%` }}
                  />
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
