'use client';

import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { Plus, FileText, Trash2, Download, Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useLessonPlans, useDeleteLessonPlan } from '@/lib/hooks/use-lesson-plans';
import { exportLessonPlanDocx } from '@/lib/api/lesson-plans';

export default function LessonPlansListPage() {
  const t = useTranslations('lessonPlan');

  const { data: plans, isLoading } = useLessonPlans();
  const deleteMutation = useDeleteLessonPlan();

  const handleDelete = (id: number) => {
    if (!confirm(t('confirmDeleteDesc'))) return;
    deleteMutation.mutate(id);
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t('myPlans')}</h1>
          <p className="text-sm text-muted-foreground">{t('myPlansSubtitle')}</p>
        </div>
        <Link href="/lesson-plans/create">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            {t('createNew')}
          </Button>
        </Link>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <FileText className="h-5 w-5" />
            {t('savedPlans')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-8">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            </div>
          ) : !plans?.length ? (
            <div className="py-8 text-center text-muted-foreground">
              {t('noPlans')}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t('topic')}</TableHead>
                  <TableHead>{t('subjectLabel')}</TableHead>
                  <TableHead>{t('language')}</TableHead>
                  <TableHead>{t('duration')}</TableHead>
                  <TableHead>{t('date')}</TableHead>
                  <TableHead className="text-right">{t('actions')}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {plans.map((plan) => (
                  <TableRow key={plan.id}>
                    <TableCell className="max-w-[300px] truncate font-medium">
                      {plan.title}
                    </TableCell>
                    <TableCell>
                      {plan.subject} {plan.grade_level && `${plan.grade_level}-сынып`}
                    </TableCell>
                    <TableCell>{plan.language === 'kk' ? 'QAZ' : 'RUS'}</TableCell>
                    <TableCell>{plan.duration_min} {t('minutes')}</TableCell>
                    <TableCell>{formatDate(plan.created_at)}</TableCell>
                    <TableCell>
                      <div className="flex justify-end gap-1">
                        <Link href={`/lesson-plans/${plan.id}`}>
                          <Button variant="ghost" size="icon">
                            <Eye className="h-4 w-4" />
                          </Button>
                        </Link>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => exportLessonPlanDocx(plan.id)}
                        >
                          <Download className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(plan.id)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
