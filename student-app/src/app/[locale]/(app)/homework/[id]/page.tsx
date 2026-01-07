'use client';

import { useParams, useRouter } from 'next/navigation';
import { useTranslations, useLocale } from 'next-intl';
import { ArrowLeft, Calendar, Award, Loader2 } from 'lucide-react';
import { Link } from '@/i18n/routing';
import { useHomeworkDetail } from '@/lib/hooks/use-homework';
import { HomeworkStatusBadge, TaskCard, LateWarning } from '@/components/homework';

export default function HomeworkDetailPage() {
  const params = useParams();
  const router = useRouter();
  const t = useTranslations('homework');
  const locale = useLocale();

  const homeworkId = params.id ? Number(params.id) : undefined;
  const { data: homework, isLoading, error } = useHomeworkDetail(homeworkId);

  const handleTaskClick = (taskId: number) => {
    router.push(`/${locale}/homework/${homeworkId}/tasks/${taskId}`);
  };

  const formatDueDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString(locale === 'kz' ? 'kk-KZ' : 'ru-RU', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 text-primary animate-spin mb-4" />
        <p className="text-gray-500">{t('loading')}</p>
      </div>
    );
  }

  if (error || !homework) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
        <p className="text-red-500 mb-4">{t('error')}</p>
        <Link
          href="/homework"
          className="text-primary hover:underline flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          {t('result.backToList')}
        </Link>
      </div>
    );
  }

  const completedTasks = homework.tasks.filter(
    (t) => t.status === 'submitted' || t.status === 'graded'
  ).length;

  return (
    <div className="mx-auto max-w-4xl px-4 py-6">
      {/* Back Button */}
      <Link
        href="/homework"
        className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        {t('result.backToList')}
      </Link>

      {/* Header */}
      <div className="card-elevated p-6 mb-6">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              {homework.title}
            </h1>
            <HomeworkStatusBadge
              status={homework.my_status}
              isOverdue={homework.is_overdue}
            />
          </div>

          {/* Score if available */}
          {homework.my_score !== null && (
            <div className="text-right">
              <p className="text-3xl font-bold text-primary">
                {homework.my_percentage?.toFixed(0)}%
              </p>
              <p className="text-sm text-gray-500">
                {homework.my_score.toFixed(1)}/{homework.max_score}
              </p>
            </div>
          )}
        </div>

        {/* Description */}
        {homework.description && (
          <p className="text-gray-600 mb-4">{homework.description}</p>
        )}

        {/* Meta Info */}
        <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            <span>{formatDueDate(homework.due_date)}</span>
          </div>
          <div className="flex items-center gap-2">
            <Award className="w-4 h-4" />
            <span>
              {completedTasks}/{homework.tasks.length} {t('task.tasks')}
            </span>
          </div>
        </div>

        {/* Late Penalty Info */}
        {homework.late_penalty > 0 && (
          <div className="mt-4 p-3 bg-red-50 rounded-lg text-sm text-red-600">
            {t('late.penaltyApplied', { percent: homework.late_penalty })}
          </div>
        )}
      </div>

      {/* Late Warning */}
      {homework.is_overdue && (
        <LateWarning
          canSubmit={homework.can_submit}
          latePenalty={homework.late_penalty}
          className="mb-6"
        />
      )}

      {/* Tasks */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">{t('task.title')}</h2>
        {homework.tasks.map((task) => (
          <TaskCard
            key={task.id}
            task={task}
            onClick={() => handleTaskClick(task.id)}
            disabled={!homework.can_submit && task.status === 'not_started'}
          />
        ))}
      </div>

      {/* All Tasks Completed Message */}
      {completedTasks === homework.tasks.length && homework.tasks.length > 0 && (
        <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-xl text-center">
          <p className="text-green-700 font-medium">{t('allTasksCompleted')}</p>
        </div>
      )}
    </div>
  );
}
