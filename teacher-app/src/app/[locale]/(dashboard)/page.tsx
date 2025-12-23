'use client';

import { useTranslations } from 'next-intl';
import { useAuth } from '@/providers/auth-provider';
import { useDashboard, useClasses } from '@/lib/hooks/use-teacher-data';
import { StatCard } from '@/components/dashboard/StatCard';
import { MasteryDistributionChart } from '@/components/dashboard/MasteryDistributionChart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { MasteryBadge } from '@/components/dashboard/MasteryBadge';
import { Link } from '@/i18n/routing';
import {
  Users,
  GraduationCap,
  BarChart3,
  AlertTriangle,
  ArrowRight,
  Loader2,
} from 'lucide-react';

export default function DashboardPage() {
  const { user } = useAuth();
  const t = useTranslations('dashboard');
  const tClasses = useTranslations('classes');

  const { data: dashboard, isLoading: dashboardLoading } = useDashboard();
  const { data: classes, isLoading: classesLoading } = useClasses();

  const isLoading = dashboardLoading || classesLoading;

  if (isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">
          {t('welcome')}, {user?.first_name}!
        </h1>
        <p className="text-muted-foreground">{t('overview')}</p>
      </div>

      {/* Stats grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title={t('classesCount')}
          value={dashboard?.classes_count ?? 0}
          icon={GraduationCap}
        />
        <StatCard
          title={t('studentsCount')}
          value={dashboard?.total_students ?? 0}
          icon={Users}
        />
        <StatCard
          title={t('averageScore')}
          value={`${Math.round(dashboard?.average_class_score ?? 0)}%`}
          icon={BarChart3}
        />
        <StatCard
          title={t('needingHelp')}
          value={dashboard?.students_needing_help ?? 0}
          icon={AlertTriangle}
          className={
            (dashboard?.students_needing_help ?? 0) > 0
              ? 'border-destructive/50'
              : ''
          }
        />
      </div>

      {/* Main content grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Classes list */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>{tClasses('title')}</CardTitle>
              <Link
                href="/classes"
                className="flex items-center gap-1 text-sm text-primary hover:underline"
              >
                {tClasses('viewClass')}
                <ArrowRight className="h-4 w-4" />
              </Link>
            </CardHeader>
            <CardContent>
              {classes && classes.length > 0 ? (
                <div className="space-y-4">
                  {classes.slice(0, 5).map((cls) => (
                    <Link
                      key={cls.id}
                      href={`/classes/${cls.id}`}
                      className="block rounded-lg border p-4 transition-colors hover:bg-muted/50"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-medium text-foreground">
                            {cls.name}
                          </h3>
                          <p className="text-sm text-muted-foreground">
                            {cls.students_count} {tClasses('students')} •{' '}
                            {cls.grade_level} класс
                          </p>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="text-right">
                            <p className="text-sm font-medium">
                              {cls.progress_percentage}%
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {tClasses('averageProgress')}
                            </p>
                          </div>
                          <Progress
                            value={cls.progress_percentage}
                            className="h-2 w-24"
                          />
                        </div>
                      </div>

                      {/* Mini mastery distribution */}
                      <div className="mt-3 flex items-center gap-2">
                        <div className="flex -space-x-1">
                          <div className="flex h-6 items-center rounded-full bg-success/10 px-2 text-xs font-medium text-success">
                            A: {cls.mastery_distribution.level_a}
                          </div>
                          <div className="flex h-6 items-center rounded-full bg-warning/10 px-2 text-xs font-medium text-warning">
                            B: {cls.mastery_distribution.level_b}
                          </div>
                          <div className="flex h-6 items-center rounded-full bg-destructive/10 px-2 text-xs font-medium text-destructive">
                            C: {cls.mastery_distribution.level_c}
                          </div>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <p className="py-8 text-center text-muted-foreground">
                  {tClasses('noClasses')}
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Mastery distribution */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>{t('masteryDistribution')}</CardTitle>
            </CardHeader>
            <CardContent>
              {dashboard?.students_by_level ? (
                <MasteryDistributionChart
                  distribution={dashboard.students_by_level}
                />
              ) : (
                <p className="py-8 text-center text-muted-foreground">
                  {t('noActivity')}
                </p>
              )}
            </CardContent>
          </Card>

          {/* Recent activity */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>{t('recentActivity')}</CardTitle>
            </CardHeader>
            <CardContent>
              {dashboard?.recent_activity && dashboard.recent_activity.length > 0 ? (
                <div className="space-y-3">
                  {dashboard.recent_activity.slice(0, 5).map((activity, i) => (
                    <div
                      key={i}
                      className="flex items-start gap-3 border-b border-border/50 pb-3 last:border-0 last:pb-0"
                    >
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
                        <Users className="h-4 w-4 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-foreground truncate">
                          {activity.student_name}
                        </p>
                        <p className="text-xs text-muted-foreground truncate">
                          {activity.description}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="py-4 text-center text-sm text-muted-foreground">
                  {t('noActivity')}
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
