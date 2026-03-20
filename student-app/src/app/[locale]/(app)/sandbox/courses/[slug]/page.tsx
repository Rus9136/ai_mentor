'use client';

import { useParams, useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import {
  ArrowLeft,
  Loader2,
  CheckCircle2,
  Circle,
  Code2,
  BookOpen,
} from 'lucide-react';
import { useCourseLessons, useCodingCourses } from '@/lib/hooks/use-coding';
import type { CodingCourse, LessonListItem } from '@/lib/api/coding';

export default function CourseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const t = useTranslations('courses');

  const slug = params.slug as string;
  const { data: courses } = useCodingCourses();
  const { data: lessons, isLoading } = useCourseLessons(slug);

  const course = courses?.find((c: CodingCourse) => c.slug === slug);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <button
          onClick={() => router.push('/sandbox/courses')}
          className="p-1.5 rounded-md hover:bg-muted transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
        </button>
        <div className="flex-1 min-w-0">
          <h1 className="text-xl font-bold truncate">
            {course?.title ?? slug}
          </h1>
          {course?.description && (
            <p className="text-sm text-muted-foreground mt-0.5">
              {course.description}
            </p>
          )}
        </div>
      </div>

      {/* Progress summary */}
      {course && (
        <div className="flex items-center gap-4 mb-6 px-4 py-3 rounded-lg bg-muted/30 border border-border">
          <div className="flex-1">
            <div className="flex items-center justify-between text-sm mb-1.5">
              <span className="text-muted-foreground">
                {t('progress')}
              </span>
              <span className="font-medium">
                {course.completed_lessons}/{course.total_lessons} {t('lessons')}
              </span>
            </div>
            <div className="h-2.5 rounded-full bg-muted overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  course.completed ? 'bg-green-500' : 'bg-primary'
                }`}
                style={{
                  width: `${
                    course.total_lessons > 0
                      ? Math.round(
                          (course.completed_lessons / course.total_lessons) * 100
                        )
                      : 0
                  }%`,
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Lessons list */}
      {!lessons?.length ? (
        <div className="text-center py-12 text-muted-foreground">
          {t('noLessons')}
        </div>
      ) : (
        <div className="space-y-2">
          {lessons.map((lesson: LessonListItem, i: number) => (
            <button
              key={lesson.id}
              onClick={() =>
                router.push(
                  `/sandbox/courses/${slug}/lessons/${lesson.id}`
                )
              }
              className="flex items-center gap-3 w-full px-4 py-3 rounded-lg border border-border hover:bg-muted/50 transition-colors text-left"
            >
              {/* Status icon */}
              {lesson.is_completed ? (
                <CheckCircle2 className="h-5 w-5 text-green-500 shrink-0" />
              ) : (
                <Circle className="h-5 w-5 text-muted-foreground/40 shrink-0" />
              )}

              {/* Number */}
              <span className="text-sm text-muted-foreground font-mono w-6 shrink-0">
                {i + 1}.
              </span>

              {/* Title */}
              <span className="flex-1 text-sm font-medium truncate">
                {lesson.title}
              </span>

              {/* Challenge indicator */}
              {lesson.has_challenge && (
                <span className="flex items-center gap-1 text-xs text-blue-500 font-medium">
                  <Code2 className="h-3.5 w-3.5" />
                  {t('hasPractice')}
                </span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
