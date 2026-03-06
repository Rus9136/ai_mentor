'use client';

import { useTranslations } from 'next-intl';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { LessonPlanData } from '@/types/lesson-plan';

interface LessonPlanViewProps {
  plan: LessonPlanData;
}

export function LessonPlanView({ plan }: LessonPlanViewProps) {
  const t = useTranslations('lessonPlan');

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg">{t('header')}</CardTitle>
        </CardHeader>
        <CardContent>
          <table className="w-full text-sm">
            <tbody>
              <HeaderRow label={t('section')} value={plan.header.section} />
              <HeaderRow label={t('topic')} value={plan.header.topic} />
              <HeaderRow label={t('learningObjective')} value={plan.header.learning_objective} />
              <HeaderRow label={t('lessonObjective')} value={plan.header.lesson_objective} />
              <HeaderRow label={t('monthlyValue')} value={`${plan.header.monthly_value} — ${plan.header.value_decomposition}`} />
            </tbody>
          </table>
        </CardContent>
      </Card>

      {/* Stages */}
      {plan.stages.map((stage, idx) => (
        <Card key={idx}>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">
                {stage.name}
                <span className="ml-2 text-sm font-normal text-muted-foreground">
                  ({stage.name_detail})
                </span>
              </CardTitle>
              <Badge variant="secondary">{stage.duration_min} {t('minutes')}</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Method info */}
            <div className="rounded-lg bg-muted/50 p-3 text-sm">
              <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
                <div>
                  <span className="font-medium">{t('method')}:</span> {stage.method_name}
                </div>
                <div>
                  <span className="font-medium">{t('purpose')}:</span> {stage.method_purpose}
                </div>
                <div>
                  <span className="font-medium">{t('effectiveness')}:</span> {stage.method_effectiveness}
                </div>
              </div>
            </div>

            {/* Activities */}
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <h4 className="mb-1 text-sm font-medium text-primary">{t('teacherActivity')}</h4>
                <p className="text-sm whitespace-pre-line">{stage.teacher_activity}</p>
              </div>
              <div>
                <h4 className="mb-1 text-sm font-medium text-primary">{t('studentActivity')}</h4>
                <p className="text-sm whitespace-pre-line">{stage.student_activity}</p>
              </div>
            </div>

            {/* Assessment */}
            <div>
              <h4 className="mb-1 text-sm font-medium">{t('assessment')}</h4>
              <p className="text-sm">{stage.assessment}</p>
            </div>

            {/* Differentiation */}
            {stage.differentiation && (
              <div>
                <h4 className="mb-1 text-sm font-medium">{t('differentiation')}</h4>
                <p className="text-sm">{stage.differentiation}</p>
              </div>
            )}

            {/* Resources */}
            <div>
              <h4 className="mb-1 text-sm font-medium">{t('resources')}</h4>
              <p className="text-sm">{stage.resources}</p>
            </div>

            {/* Tasks */}
            {stage.tasks.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-medium">{t('tasks')}</h4>
                <div className="space-y-3">
                  {stage.tasks.map((task) => (
                    <div key={task.number} className="rounded-lg border p-3">
                      <div className="mb-2 flex items-center justify-between">
                        <span className="text-sm font-medium">
                          {t('task')} {task.number}
                        </span>
                        <Badge>{task.total_score} {t('score')}</Badge>
                      </div>
                      <div className="mb-2 grid grid-cols-1 gap-3 text-sm md:grid-cols-2">
                        <div>
                          <span className="font-medium text-primary">{t('teacherActivity')}:</span>
                          <p className="mt-0.5 whitespace-pre-line">{task.teacher_activity}</p>
                        </div>
                        <div>
                          <span className="font-medium text-primary">{t('studentActivity')}:</span>
                          <p className="mt-0.5 whitespace-pre-line">{task.student_activity}</p>
                        </div>
                      </div>
                      {task.descriptors.length > 0 && (
                        <div className="mt-2">
                          <span className="text-xs font-medium text-muted-foreground">{t('descriptors')}:</span>
                          <ul className="mt-1 space-y-1">
                            {task.descriptors.map((d, di) => (
                              <li key={di} className="flex items-start gap-2 text-xs">
                                <Badge variant="outline" className="shrink-0">{d.score}</Badge>
                                <span>{d.text}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      ))}

      {/* Total score */}
      <div className="flex items-center justify-between rounded-lg border bg-primary/5 p-4">
        <span className="text-sm font-medium">{t('totalScore')}</span>
        <Badge className="text-lg">{plan.total_score} {t('score')}</Badge>
      </div>

      {/* Differentiation block */}
      {plan.differentiation && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">{t('differentiation')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <p>{plan.differentiation.approach}</p>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              <div className="rounded-lg bg-green-50 p-3 dark:bg-green-950/20">
                <span className="font-medium text-green-700 dark:text-green-400">A:</span>{' '}
                {plan.differentiation.for_level_a}
              </div>
              <div className="rounded-lg bg-yellow-50 p-3 dark:bg-yellow-950/20">
                <span className="font-medium text-yellow-700 dark:text-yellow-400">B:</span>{' '}
                {plan.differentiation.for_level_b}
              </div>
              <div className="rounded-lg bg-red-50 p-3 dark:bg-red-950/20">
                <span className="font-medium text-red-700 dark:text-red-400">C:</span>{' '}
                {plan.differentiation.for_level_c}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Health & Safety */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg">{t('healthSafety')}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm">{plan.health_safety}</p>
        </CardContent>
      </Card>

      {/* Reflection */}
      {plan.reflection_template.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">{t('reflection')}</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc space-y-1 pl-5 text-sm">
              {plan.reflection_template.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function HeaderRow({ label, value }: { label: string; value: string }) {
  return (
    <tr className="border-b last:border-0">
      <td className="w-1/3 py-2 pr-4 font-medium text-muted-foreground">{label}</td>
      <td className="py-2">{value}</td>
    </tr>
  );
}
