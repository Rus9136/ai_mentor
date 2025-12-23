'use client';

import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useClassDetail } from '@/lib/hooks/use-teacher-data';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { MasteryDistributionChart } from '@/components/dashboard/MasteryDistributionChart';
import { MasteryBadge } from '@/components/dashboard/MasteryBadge';
import { Button } from '@/components/ui/button';
import { Link } from '@/i18n/routing';
import {
  ArrowLeft,
  Users,
  Loader2,
  ChevronRight,
} from 'lucide-react';
import { formatRelativeDate } from '@/lib/utils';

export default function ClassDetailPage() {
  const params = useParams();
  const classId = Number(params.id);
  const t = useTranslations('classes');
  const tStudent = useTranslations('student');

  const { data: classData, isLoading, error } = useClassDetail(classId);

  if (isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !classData) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center">
        <p className="text-muted-foreground">Class not found</p>
        <Link href="/classes">
          <Button variant="link" className="mt-2">
            <ArrowLeft className="mr-2 h-4 w-4" />
            {t('title')}
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/classes">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-5 w-5" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-foreground">{classData.name}</h1>
          <p className="text-muted-foreground">
            {classData.grade_level} класс • {classData.academic_year}
          </p>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-primary/10 p-2">
                <Users className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold">{classData.students_count}</p>
                <p className="text-sm text-muted-foreground">{t('students')}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="text-2xl font-bold">{classData.progress_percentage}%</p>
            <p className="text-sm text-muted-foreground">{t('averageProgress')}</p>
            <Progress value={classData.progress_percentage} className="mt-2 h-2" />
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardContent className="pt-6">
            <p className="mb-2 text-sm font-medium text-muted-foreground">
              Распределение по уровням
            </p>
            <MasteryDistributionChart distribution={classData.mastery_distribution} />
          </CardContent>
        </Card>
      </div>

      {/* Students table */}
      <Card>
        <CardHeader>
          <CardTitle>{t('studentsList')}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Ученик</th>
                  <th>{t('masteryLevel')}</th>
                  <th>{t('progress')}</th>
                  <th>{t('lastActivity')}</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {classData.students.map((student) => (
                  <tr key={student.id}>
                    <td>
                      <div className="flex items-center gap-3">
                        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-sm font-medium text-primary">
                          {student.first_name[0]}
                          {student.last_name[0]}
                        </div>
                        <div>
                          <p className="font-medium text-foreground">
                            {student.last_name} {student.first_name}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {student.student_code}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td>
                      <MasteryBadge level={student.mastery_level} showLabel />
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        <Progress
                          value={student.progress_percentage}
                          className="h-2 w-20"
                        />
                        <span className="text-sm text-muted-foreground">
                          {student.progress_percentage}%
                        </span>
                      </div>
                    </td>
                    <td>
                      <span className="text-sm text-muted-foreground">
                        {student.last_activity
                          ? formatRelativeDate(student.last_activity)
                          : t('neverActive')}
                      </span>
                    </td>
                    <td>
                      <Link
                        href={`/classes/${classId}/students/${student.id}`}
                        className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
                      >
                        Подробнее
                        <ChevronRight className="h-4 w-4" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
