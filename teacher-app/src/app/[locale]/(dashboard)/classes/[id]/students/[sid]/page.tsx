'use client';

import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useStudentProgress, useMasteryHistory } from '@/lib/hooks/use-teacher-data';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { MasteryBadge } from '@/components/dashboard/MasteryBadge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Link } from '@/i18n/routing';
import {
  ArrowLeft,
  Loader2,
  Clock,
  BookOpen,
  TrendingUp,
  TrendingDown,
  Minus,
} from 'lucide-react';
import { formatRelativeDate } from '@/lib/utils';

export default function StudentProgressPage() {
  const params = useParams();
  const classId = Number(params.id);
  const studentId = Number(params.sid);
  const t = useTranslations('student');
  const tClasses = useTranslations('classes');

  const { data: progress, isLoading } = useStudentProgress(classId, studentId);
  const { data: masteryHistory } = useMasteryHistory(studentId);

  if (isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!progress) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center">
        <p className="text-muted-foreground">Student not found</p>
        <Link href={`/classes/${classId}`}>
          <Button variant="link" className="mt-2">
            <ArrowLeft className="mr-2 h-4 w-4" />
            {tClasses('classDetail')}
          </Button>
        </Link>
      </div>
    );
  }

  const studentName = `${progress.student.last_name} ${progress.student.first_name}`;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href={`/classes/${classId}`}>
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-5 w-5" />
          </Button>
        </Link>
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-lg font-semibold text-primary">
            {progress.student.first_name[0]}
            {progress.student.last_name[0]}
          </div>
          <div>
            <h1 className="text-2xl font-bold text-foreground">{studentName}</h1>
            <p className="text-muted-foreground">
              {progress.class_name} • {progress.student.student_code}
            </p>
          </div>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">{t('overallMastery')}</p>
            <div className="mt-2 flex items-center gap-3">
              <MasteryBadge level={progress.overall_mastery_level} size="lg" />
              <span className="text-2xl font-bold">
                {Math.round(progress.overall_mastery_score)}%
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">{t('timeSpent')}</p>
            </div>
            <p className="mt-2 text-2xl font-bold">
              {Math.round(progress.total_time_spent / 60)} {t('minutes')}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">{tClasses('progress')}</p>
            </div>
            <p className="mt-2 text-2xl font-bold">
              {progress.chapters_progress.filter((c) => c.progress_percentage === 100).length}/
              {progress.chapters_progress.length}
            </p>
            <p className="text-xs text-muted-foreground">глав завершено</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">{tClasses('lastActivity')}</p>
            <p className="mt-2 text-lg font-medium">
              {progress.last_activity
                ? formatRelativeDate(progress.last_activity)
                : tClasses('neverActive')}
            </p>
            {progress.days_since_last_activity > 7 && (
              <p className="text-xs text-destructive">
                {progress.days_since_last_activity} дней неактивен
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="chapters">
        <TabsList>
          <TabsTrigger value="chapters">{t('chaptersProgress')}</TabsTrigger>
          <TabsTrigger value="tests">{t('recentTests')}</TabsTrigger>
          <TabsTrigger value="history">{t('masteryHistory')}</TabsTrigger>
        </TabsList>

        {/* Chapters Progress */}
        <TabsContent value="chapters">
          <Card>
            <CardContent className="pt-6">
              <div className="space-y-4">
                {progress.chapters_progress.map((chapter) => (
                  <div
                    key={chapter.chapter_id}
                    className="flex items-center gap-4 rounded-lg border p-4"
                  >
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted text-sm font-bold">
                      {chapter.chapter_number}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium">{chapter.chapter_title}</p>
                      <div className="mt-2 flex items-center gap-3">
                        <Progress
                          value={chapter.progress_percentage}
                          className="h-2 flex-1"
                        />
                        <span className="text-sm text-muted-foreground">
                          {chapter.progress_percentage}%
                        </span>
                      </div>
                    </div>
                    <MasteryBadge level={chapter.mastery_level} />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Recent Tests */}
        <TabsContent value="tests">
          <Card>
            <CardContent className="pt-6">
              {progress.recent_tests.length > 0 ? (
                <div className="space-y-3">
                  {progress.recent_tests.map((test) => (
                    <div
                      key={test.id}
                      className="flex items-center justify-between rounded-lg border p-4"
                    >
                      <div>
                        <p className="font-medium">{test.test_title}</p>
                        <p className="text-sm text-muted-foreground">
                          {formatRelativeDate(test.completed_at)}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold">
                          {test.score}/{test.max_score}
                        </p>
                        <p
                          className={`text-sm ${
                            test.percentage >= 85
                              ? 'text-success'
                              : test.percentage >= 60
                              ? 'text-warning'
                              : 'text-destructive'
                          }`}
                        >
                          {Math.round(test.percentage)}%
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="py-8 text-center text-muted-foreground">
                  {t('noTests')}
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Mastery History */}
        <TabsContent value="history">
          <Card>
            <CardContent className="pt-6">
              {masteryHistory?.history && masteryHistory.history.length > 0 ? (
                <div className="relative space-y-4 pl-6 before:absolute before:left-2 before:top-2 before:h-[calc(100%-16px)] before:w-0.5 before:bg-border">
                  {masteryHistory.history.map((item) => {
                    const isImprovement =
                      item.new_score &&
                      item.previous_score &&
                      item.new_score > item.previous_score;
                    const isDecline =
                      item.new_score &&
                      item.previous_score &&
                      item.new_score < item.previous_score;

                    return (
                      <div key={item.id} className="relative flex gap-4">
                        <div className="absolute -left-4 flex h-4 w-4 items-center justify-center rounded-full bg-background ring-2 ring-border">
                          {isImprovement && (
                            <TrendingUp className="h-3 w-3 text-success" />
                          )}
                          {isDecline && (
                            <TrendingDown className="h-3 w-3 text-destructive" />
                          )}
                          {!isImprovement && !isDecline && (
                            <Minus className="h-3 w-3 text-muted-foreground" />
                          )}
                        </div>
                        <div className="flex-1 rounded-lg border p-3">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              {item.previous_level && (
                                <MasteryBadge level={item.previous_level} size="sm" />
                              )}
                              {item.new_level && item.previous_level && (
                                <span className="text-muted-foreground">→</span>
                              )}
                              {item.new_level && (
                                <MasteryBadge level={item.new_level} size="sm" />
                              )}
                            </div>
                            <span className="text-xs text-muted-foreground">
                              {formatRelativeDate(item.recorded_at)}
                            </span>
                          </div>
                          {item.new_score !== null && (
                            <p className="mt-1 text-sm text-muted-foreground">
                              Балл: {Math.round(item.new_score)}%
                              {item.previous_score !== null && (
                                <span
                                  className={
                                    isImprovement
                                      ? 'text-success'
                                      : isDecline
                                      ? 'text-destructive'
                                      : ''
                                  }
                                >
                                  {' '}
                                  ({isImprovement ? '+' : ''}
                                  {Math.round(item.new_score - item.previous_score)}%)
                                </span>
                              )}
                            </p>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="py-8 text-center text-muted-foreground">
                  Нет истории изменений
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
