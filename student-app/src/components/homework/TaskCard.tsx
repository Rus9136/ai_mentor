'use client';

import { useTranslations } from 'next-intl';
import {
  BookOpen,
  ClipboardList,
  MessageSquare,
  FileText,
  Code,
  Dumbbell,
  Clock,
  Award,
  CheckCircle2,
  PlayCircle,
  RotateCcw,
} from 'lucide-react';
import { StudentTaskResponse, TaskType, SubmissionStatus } from '@/lib/api/homework';
import { cn } from '@/lib/utils';

interface TaskCardProps {
  task: StudentTaskResponse;
  onClick: () => void;
  disabled?: boolean;
}

const taskTypeIcons: Record<TaskType, typeof BookOpen> = {
  [TaskType.READ]: BookOpen,
  [TaskType.QUIZ]: ClipboardList,
  [TaskType.OPEN_QUESTION]: MessageSquare,
  [TaskType.ESSAY]: FileText,
  [TaskType.PRACTICE]: Dumbbell,
  [TaskType.CODE]: Code,
};

const statusStyles: Record<SubmissionStatus, string> = {
  [SubmissionStatus.NOT_STARTED]: 'border-gray-200 bg-white',
  [SubmissionStatus.IN_PROGRESS]: 'border-amber-200 bg-amber-50/50',
  [SubmissionStatus.SUBMITTED]: 'border-green-200 bg-green-50/50',
  [SubmissionStatus.GRADED]: 'border-purple-200 bg-purple-50/50',
};

export function TaskCard({ task, onClick, disabled }: TaskCardProps) {
  const t = useTranslations('homework');
  const tTask = useTranslations('homework.taskType');

  const Icon = taskTypeIcons[task.task_type] || ClipboardList;

  const getActionButton = () => {
    switch (task.status) {
      case SubmissionStatus.NOT_STARTED:
        return (
          <button
            onClick={onClick}
            disabled={disabled || task.attempts_remaining === 0}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-colors',
              task.attempts_remaining > 0
                ? 'bg-primary text-white hover:bg-primary/90'
                : 'bg-gray-100 text-gray-400 cursor-not-allowed'
            )}
          >
            <PlayCircle className="w-4 h-4" />
            {t('task.start')}
          </button>
        );
      case SubmissionStatus.IN_PROGRESS:
        return (
          <button
            onClick={onClick}
            disabled={disabled}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium bg-amber-500 text-white hover:bg-amber-600 transition-colors"
          >
            <PlayCircle className="w-4 h-4" />
            {t('task.continue')}
          </button>
        );
      case SubmissionStatus.SUBMITTED:
      case SubmissionStatus.GRADED:
        return (
          <div className="flex items-center gap-2">
            {task.attempts_remaining > 0 && (
              <button
                onClick={onClick}
                disabled={disabled}
                className="flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
              >
                <RotateCcw className="w-4 h-4" />
                {t('task.tryAgain')}
              </button>
            )}
            <button
              onClick={onClick}
              disabled={disabled}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium bg-primary/10 text-primary hover:bg-primary/20 transition-colors"
            >
              <CheckCircle2 className="w-4 h-4" />
              {t('task.viewResults')}
            </button>
          </div>
        );
    }
  };

  return (
    <div
      className={cn(
        'rounded-xl border-2 p-4 transition-all',
        statusStyles[task.status]
      )}
    >
      <div className="flex items-start gap-4">
        {/* Icon */}
        <div
          className={cn(
            'w-12 h-12 rounded-xl flex items-center justify-center shrink-0',
            task.status === SubmissionStatus.NOT_STARTED
              ? 'bg-gray-100 text-gray-500'
              : task.status === SubmissionStatus.IN_PROGRESS
              ? 'bg-amber-100 text-amber-600'
              : 'bg-green-100 text-green-600'
          )}
        >
          <Icon className="w-6 h-6" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Title */}
          <h4 className="font-semibold text-gray-900 mb-1">
            {task.paragraph_title || tTask(task.task_type)}
          </h4>

          {/* Instructions */}
          {task.instructions && (
            <p className="text-sm text-gray-500 line-clamp-2 mb-2">
              {task.instructions}
            </p>
          )}

          {/* Meta Info */}
          <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
            {/* Points */}
            <div className="flex items-center gap-1">
              <Award className="w-3.5 h-3.5" />
              <span>{t('task.points', { count: task.points })}</span>
            </div>

            {/* Questions Count */}
            <div className="flex items-center gap-1">
              <ClipboardList className="w-3.5 h-3.5" />
              <span>{t('task.questions', { count: task.questions_count })}</span>
            </div>

            {/* Time Limit */}
            {task.time_limit_minutes && (
              <div className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" />
                <span>{t('task.timeLimit', { minutes: task.time_limit_minutes })}</span>
              </div>
            )}

            {/* Attempts */}
            <div className="flex items-center gap-1">
              <RotateCcw className="w-3.5 h-3.5" />
              <span>
                {t('task.attempt', {
                  current: task.current_attempt,
                  max: task.max_attempts,
                })}
              </span>
            </div>

            {/* Score if graded */}
            {task.my_score !== null && (
              <div className="flex items-center gap-1 text-primary font-medium">
                <span>
                  {task.my_score.toFixed(1)}/{task.points}
                </span>
              </div>
            )}
          </div>

          {/* Progress if in progress */}
          {task.status === SubmissionStatus.IN_PROGRESS && task.questions_count > 0 && (
            <div className="mt-2">
              <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-amber-500 transition-all duration-300"
                  style={{
                    width: `${(task.answered_count / task.questions_count) * 100}%`,
                  }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">
                {task.answered_count}/{task.questions_count}
              </p>
            </div>
          )}
        </div>

        {/* Action Button */}
        <div className="shrink-0">{getActionButton()}</div>
      </div>
    </div>
  );
}
