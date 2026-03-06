'use client';

import { useState, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { Loader2, FileText, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ContentSelector, ContentSelection } from '@/components/homework/ContentSelector';
import { LessonPlanView } from '@/components/lesson-plan/LessonPlanView';
import { useClasses } from '@/lib/hooks/use-teacher-data';
import { useGenerateLessonPlan } from '@/lib/hooks/use-lesson-plans';
import type { LessonPlanGenerateResponse } from '@/types/lesson-plan';

export default function LessonPlanCreatePage() {
  const t = useTranslations('lessonPlan');

  const [selection, setSelection] = useState<ContentSelection>({});
  const [classId, setClassId] = useState<string>('none');
  const [language, setLanguage] = useState<string>('kk');
  const [durationMin, setDurationMin] = useState<string>('40');
  const [result, setResult] = useState<LessonPlanGenerateResponse | null>(null);

  const { data: classes } = useClasses();
  const mutation = useGenerateLessonPlan();

  const handleSelect = useCallback((sel: ContentSelection) => {
    setSelection(sel);
  }, []);

  const handleGenerate = () => {
    if (!selection.paragraphId) return;
    mutation.mutate(
      {
        paragraph_id: selection.paragraphId,
        class_id: classId !== 'none' ? Number(classId) : undefined,
        language,
        duration_min: Number(durationMin),
      },
      {
        onSuccess: (data) => setResult(data),
      }
    );
  };

  const canGenerate = !!selection.paragraphId && !mutation.isPending;

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold">{t('title')}</h1>
        <p className="text-sm text-muted-foreground">{t('subtitle')}</p>
      </div>

      {/* Form */}
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2 text-base">
            <FileText className="h-5 w-5" />
            {t('title')}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Content selector (textbook -> chapter -> paragraph) */}
          <ContentSelector onSelect={handleSelect} disabled={mutation.isPending} />

          {/* Class selector */}
          <div className="space-y-2">
            <Label>{t('selectClass')}</Label>
            <Select value={classId} onValueChange={setClassId} disabled={mutation.isPending}>
              <SelectTrigger>
                <SelectValue placeholder={t('selectClass')} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">{t('noClass')}</SelectItem>
                {classes?.map((cls) => (
                  <SelectItem key={cls.id} value={cls.id.toString()}>
                    {cls.name} ({cls.students_count} {t('students')})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Language & Duration */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>{t('language')}</Label>
              <Select value={language} onValueChange={setLanguage} disabled={mutation.isPending}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="kk">{t('langKk')}</SelectItem>
                  <SelectItem value="ru">{t('langRu')}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>{t('duration')}</Label>
              <Select value={durationMin} onValueChange={setDurationMin} disabled={mutation.isPending}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="40">40 {t('minutes')}</SelectItem>
                  <SelectItem value="45">45 {t('minutes')}</SelectItem>
                  <SelectItem value="80">80 {t('minutes')}</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Generate button */}
          <Button
            onClick={handleGenerate}
            disabled={!canGenerate}
            className="w-full"
            size="lg"
          >
            {mutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {t('generating')}
              </>
            ) : result ? (
              <>
                <RefreshCw className="mr-2 h-4 w-4" />
                {t('regenerate')}
              </>
            ) : (
              t('generate')
            )}
          </Button>

          {/* Error */}
          {mutation.isError && (
            <p className="text-sm text-destructive">{t('errorGeneration')}</p>
          )}
        </CardContent>
      </Card>

      {/* Mastery distribution */}
      {result?.context.mastery_distribution && result.context.total_students && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">{t('masteryDistribution')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <MasteryBar
                label={t('levelA')}
                count={result.context.mastery_distribution.A || 0}
                total={result.context.total_students}
                color="bg-green-500"
              />
              <MasteryBar
                label={t('levelB')}
                count={result.context.mastery_distribution.B || 0}
                total={result.context.total_students}
                color="bg-yellow-500"
              />
              <MasteryBar
                label={t('levelC')}
                count={result.context.mastery_distribution.C || 0}
                total={result.context.total_students}
                color="bg-red-500"
              />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Generated plan */}
      {result && <LessonPlanView plan={result.lesson_plan} />}
    </div>
  );
}

function MasteryBar({
  label,
  count,
  total,
  color,
}: {
  label: string;
  count: number;
  total: number;
  color: string;
}) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div className="flex items-center gap-3">
      <span className="w-44 text-sm">{label}</span>
      <div className="h-5 flex-1 rounded-full bg-muted">
        <div
          className={`h-5 rounded-full ${color} transition-all`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-20 text-right text-sm">
        {count} ({pct}%)
      </span>
    </div>
  );
}
