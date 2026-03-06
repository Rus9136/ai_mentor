'use client';

import { useParams, useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { ArrowLeft, Download, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { LessonPlanView } from '@/components/lesson-plan/LessonPlanView';
import { useLessonPlan, useDeleteLessonPlan } from '@/lib/hooks/use-lesson-plans';
import { exportLessonPlanDocx } from '@/lib/api/lesson-plans';
import type { LessonPlanData } from '@/types/lesson-plan';

export default function LessonPlanDetailPage() {
  const params = useParams();
  const router = useRouter();
  const t = useTranslations('lessonPlan');
  const planId = Number(params.id);

  const { data: plan, isLoading } = useLessonPlan(planId || null);
  const deleteMutation = useDeleteLessonPlan();

  const handleDelete = () => {
    if (!confirm(t('confirmDeleteDesc'))) return;
    deleteMutation.mutate(planId, {
      onSuccess: () => router.push('/lesson-plans'),
    });
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!plan) {
    return (
      <div className="py-16 text-center text-muted-foreground">
        {t('planNotFound')}
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => router.push('/lesson-plans')}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">{plan.title}</h1>
            <p className="text-sm text-muted-foreground">
              {plan.context_data.subject} {plan.context_data.grade_level}-{t('classLabel')} | {plan.language === 'kk' ? 'QAZ' : 'RUS'} | {plan.duration_min} {t('minutes')}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => exportLessonPlanDocx(plan.id)}>
            <Download className="mr-2 h-4 w-4" />
            {t('exportDocx')}
          </Button>
          <Button variant="destructive" onClick={handleDelete}>
            <Trash2 className="mr-2 h-4 w-4" />
            {t('delete')}
          </Button>
        </div>
      </div>

      <LessonPlanView plan={plan.plan_data as LessonPlanData} />
    </div>
  );
}
