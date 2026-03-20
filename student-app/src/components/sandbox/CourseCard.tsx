'use client';

import { useTranslations } from 'next-intl';
import { BookOpen, CheckCircle2, Clock, GraduationCap } from 'lucide-react';
import type { CodingCourse } from '@/lib/api/coding';
import { useRouter } from 'next/navigation';

interface CourseCardProps {
  course: CodingCourse;
}

export function CourseCard({ course }: CourseCardProps) {
  const t = useTranslations('courses');
  const router = useRouter();

  const progress =
    course.total_lessons > 0
      ? Math.round((course.completed_lessons / course.total_lessons) * 100)
      : 0;

  return (
    <button
      onClick={() => router.push(`/sandbox/courses/${course.slug}`)}
      className="flex flex-col w-full p-5 rounded-xl border border-border hover:border-primary/30 hover:shadow-sm transition-all text-left bg-card"
    >
      {/* Icon + title */}
      <div className="flex items-start gap-3 mb-3">
        <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 shrink-0">
          {course.completed ? (
            <CheckCircle2 className="h-5 w-5 text-green-500" />
          ) : (
            <GraduationCap className="h-5 w-5 text-blue-600" />
          )}
        </div>
        <div className="min-w-0">
          <h3 className="font-semibold text-sm leading-tight truncate">
            {course.title}
          </h3>
          {course.description && (
            <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
              {course.description}
            </p>
          )}
        </div>
      </div>

      {/* Meta row */}
      <div className="flex items-center gap-3 text-xs text-muted-foreground mb-3">
        {course.grade_level && (
          <span>{t('grade', { n: course.grade_level })}</span>
        )}
        <span className="flex items-center gap-1">
          <BookOpen className="h-3 w-3" />
          {t('lessonsCount', { n: course.total_lessons })}
        </span>
        {course.estimated_hours && (
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {t('hours', { n: course.estimated_hours })}
          </span>
        )}
      </div>

      {/* Progress bar */}
      <div className="w-full">
        <div className="flex items-center justify-between text-xs mb-1">
          <span className="text-muted-foreground">
            {course.completed_lessons}/{course.total_lessons} {t('lessons')}
          </span>
          <span className="font-medium">
            {progress}%
          </span>
        </div>
        <div className="h-2 rounded-full bg-muted overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              course.completed
                ? 'bg-green-500'
                : progress > 0
                ? 'bg-primary'
                : 'bg-muted'
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Action hint */}
      <div className="mt-3 text-xs font-medium text-primary">
        {course.completed
          ? t('reviewCourse')
          : course.started
          ? t('continue')
          : t('start')}
      </div>
    </button>
  );
}
