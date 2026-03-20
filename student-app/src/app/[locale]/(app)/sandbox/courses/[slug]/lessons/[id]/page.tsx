'use client';

import { useParams, useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { useLessonDetail, useCourseLessons } from '@/lib/hooks/use-coding';
import { LessonView } from '@/components/sandbox/LessonView';
import { useCallback, useMemo } from 'react';

export default function LessonPage() {
  const params = useParams();
  const router = useRouter();
  const t = useTranslations('courses');

  const slug = params.slug as string;
  const lessonId = Number(params.id);

  const { data: lesson, isLoading: lessonLoading } = useLessonDetail(
    isNaN(lessonId) ? undefined : lessonId
  );
  const { data: lessons } = useCourseLessons(slug);

  // Find current lesson index for prev/next navigation
  const { prevId, nextId, lessonNumber, totalLessons } = useMemo(() => {
    if (!lessons) return { prevId: null, nextId: null, lessonNumber: 0, totalLessons: 0 };
    const idx = lessons.findIndex((l) => l.id === lessonId);
    return {
      prevId: idx > 0 ? lessons[idx - 1].id : null,
      nextId: idx < lessons.length - 1 ? lessons[idx + 1].id : null,
      lessonNumber: idx + 1,
      totalLessons: lessons.length,
    };
  }, [lessons, lessonId]);

  const navigateTo = useCallback(
    (id: number | null) => {
      if (id) {
        router.push(`/sandbox/courses/${slug}/lessons/${id}`);
      }
    },
    [router, slug]
  );

  if (lessonLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!lesson) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        {t('lessonNotFound')}
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-5rem)] md:h-[calc(100vh-4rem)]">
      {/* Header bar */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
        <button
          onClick={() => router.push(`/sandbox/courses/${slug}`)}
          className="p-1.5 rounded-md hover:bg-muted transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
        </button>

        <div className="flex-1 min-w-0">
          <h1 className="text-sm font-semibold truncate">{lesson.title}</h1>
          <p className="text-xs text-muted-foreground">
            {t('lessonOf', { n: lessonNumber, total: totalLessons })}
          </p>
        </div>
      </div>

      {/* Lesson content */}
      <div className="flex-1 min-h-0">
        <LessonView
          lesson={lesson}
          courseSlug={slug}
          onNext={() => navigateTo(nextId)}
          onPrev={() => navigateTo(prevId)}
          hasNext={nextId !== null}
          hasPrev={prevId !== null}
          lessonNumber={lessonNumber}
          totalLessons={totalLessons}
        />
      </div>
    </div>
  );
}
