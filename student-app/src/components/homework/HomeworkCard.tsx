'use client';

import { useTranslations, useLocale } from 'next-intl';
import { Link } from '@/i18n/routing';
import { Calendar, FileText, Award, AlertTriangle } from 'lucide-react';
import { StudentHomeworkResponse } from '@/lib/api/homework';
import { HomeworkStatusBadge } from './HomeworkStatusBadge';
import { cn } from '@/lib/utils';

interface HomeworkCardProps {
  homework: StudentHomeworkResponse;
}

export function HomeworkCard({ homework }: HomeworkCardProps) {
  const t = useTranslations('homework');
  const locale = useLocale();

  const dueDate = new Date(homework.due_date);
  const now = new Date();
  const daysLeft = Math.ceil(
    (dueDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
  );
  const hoursLeft = Math.ceil(
    (dueDate.getTime() - now.getTime()) / (1000 * 60 * 60)
  );

  const formatDueDate = () => {
    return dueDate.toLocaleDateString(locale === 'kz' ? 'kk-KZ' : 'ru-RU', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const completedTasks = homework.tasks.filter(
    (t) => t.status === 'submitted' || t.status === 'graded'
  ).length;
  const totalTasks = homework.tasks.length;
  const progress = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;

  return (
    <Link href={`/homework/${homework.id}`}>
      <div
        className={cn(
          'card-elevated p-4 hover:shadow-lg transition-shadow cursor-pointer',
          homework.is_overdue && homework.can_submit && 'border-l-4 border-l-amber-400',
          homework.is_overdue && !homework.can_submit && 'border-l-4 border-l-red-400 opacity-75'
        )}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <h3 className="font-semibold text-gray-900 line-clamp-2">
            {homework.title}
          </h3>
          <HomeworkStatusBadge
            status={homework.my_status}
            isOverdue={homework.is_overdue}
          />
        </div>

        {/* Description */}
        {homework.description && (
          <p className="text-sm text-gray-500 line-clamp-2 mb-3">
            {homework.description}
          </p>
        )}

        {/* Progress Bar */}
        <div className="mb-3">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>
              {completedTasks}/{totalTasks} {t('task.tasks')}
            </span>
            {homework.my_score !== null && (
              <span className="font-medium text-gray-700">
                {homework.my_score.toFixed(1)}/{homework.max_score}
              </span>
            )}
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Footer Info */}
        <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
          {/* Due Date */}
          <div
            className={cn(
              'flex items-center gap-1',
              homework.is_overdue ? 'text-red-600' : ''
            )}
          >
            <Calendar className="w-3.5 h-3.5" />
            <span>{formatDueDate()}</span>
          </div>

          {/* Time Left */}
          {!homework.is_overdue && daysLeft <= 3 && (
            <div className="flex items-center gap-1 text-amber-600">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>
                {daysLeft > 0
                  ? t('daysLeft', { count: daysLeft })
                  : hoursLeft > 0
                  ? t('hoursLeft', { count: hoursLeft })
                  : t('overdue')}
              </span>
            </div>
          )}

          {/* Tasks Count */}
          <div className="flex items-center gap-1">
            <FileText className="w-3.5 h-3.5" />
            <span>
              {totalTasks} {t('task.tasks')}
            </span>
          </div>

          {/* Score if graded */}
          {homework.my_percentage !== null && (
            <div className="flex items-center gap-1 text-primary font-medium">
              <Award className="w-3.5 h-3.5" />
              <span>{homework.my_percentage.toFixed(0)}%</span>
            </div>
          )}

          {/* Late Penalty */}
          {homework.late_penalty > 0 && (
            <div className="flex items-center gap-1 text-red-600">
              <span>-{homework.late_penalty}%</span>
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}
