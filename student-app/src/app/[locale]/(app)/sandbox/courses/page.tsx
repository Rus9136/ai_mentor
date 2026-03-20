'use client';

import { useTranslations } from 'next-intl';
import { GraduationCap, Loader2, Code2, ListChecks } from 'lucide-react';
import { useCodingCourses } from '@/lib/hooks/use-coding';
import { CourseCard } from '@/components/sandbox/CourseCard';
import { useRouter } from 'next/navigation';

export default function CoursesPage() {
  const t = useTranslations('courses');
  const router = useRouter();
  const { data: courses, isLoading } = useCodingCourses();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/30">
            <GraduationCap className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold">{t('title')}</h1>
            <p className="text-sm text-muted-foreground">{t('subtitle')}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => router.push('/sandbox/challenges')}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:bg-muted transition-colors"
          >
            <ListChecks className="h-4 w-4" />
            {t('challenges')}
          </button>
          <button
            onClick={() => router.push('/sandbox')}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:bg-muted transition-colors"
          >
            <Code2 className="h-4 w-4" />
            {t('sandbox')}
          </button>
        </div>
      </div>

      {/* Courses grid */}
      {!courses?.length ? (
        <div className="text-center py-12 text-muted-foreground">
          {t('noCourses')}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {courses.map((course) => (
            <CourseCard key={course.id} course={course} />
          ))}
        </div>
      )}
    </div>
  );
}
