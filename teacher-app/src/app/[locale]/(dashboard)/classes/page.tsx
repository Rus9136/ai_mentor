'use client';

import { useTranslations } from 'next-intl';
import { useClasses } from '@/lib/hooks/use-teacher-data';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { MasteryDistributionChart } from '@/components/dashboard/MasteryDistributionChart';
import { Link } from '@/i18n/routing';
import { Users, ArrowRight, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function ClassesPage() {
  const t = useTranslations('classes');
  const { data: classes, isLoading } = useClasses();

  if (isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">{t('title')}</h1>
      </div>

      {classes && classes.length > 0 ? (
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {classes.map((cls) => (
            <Card key={cls.id} className="overflow-hidden">
              <CardHeader className="bg-primary/5 pb-3">
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg">{cls.name}</CardTitle>
                    <p className="text-sm text-muted-foreground">
                      {cls.grade_level} класс • {cls.academic_year}
                    </p>
                  </div>
                  <div className="rounded-lg bg-primary/10 p-2">
                    <Users className="h-5 w-5 text-primary" />
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-4">
                {/* Students count and progress */}
                <div className="mb-4 flex items-center justify-between">
                  <div>
                    <p className="text-2xl font-bold text-foreground">
                      {cls.students_count}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {t('students')}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-foreground">
                      {cls.progress_percentage}%
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {t('averageProgress')}
                    </p>
                  </div>
                </div>

                {/* Progress bar */}
                <Progress value={cls.progress_percentage} className="mb-4 h-2" />

                {/* Mastery distribution */}
                <MasteryDistributionChart distribution={cls.mastery_distribution} />

                {/* View button */}
                <Link
                  href={`/classes/${cls.id}`}
                  className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-primary/10 py-2 text-sm font-medium text-primary transition-colors hover:bg-primary/20"
                >
                  {t('viewClass')}
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="py-12 text-center">
            <Users className="mx-auto mb-4 h-12 w-12 text-muted-foreground/50" />
            <p className="text-muted-foreground">{t('noClasses')}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
