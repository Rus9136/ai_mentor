'use client';

import { useState, useMemo } from 'react';
import { useTranslations } from 'next-intl';
import { Star, BookOpen } from 'lucide-react';
import { useExercises } from '@/lib/hooks/use-textbooks';
import { renderMathInHtml } from '@/components/common/MathText';
import { Loader2 } from 'lucide-react';

interface ExerciseListProps {
  paragraphId: number;
}

type DifficultyFilter = 'all' | 'A' | 'B' | 'C';

const difficultyColors: Record<string, string> = {
  A: 'bg-green-100 text-green-700',
  B: 'bg-amber-100 text-amber-700',
  C: 'bg-red-100 text-red-700',
};

export default function ExerciseList({ paragraphId }: ExerciseListProps) {
  const t = useTranslations('paragraph.exercises');
  const { data, isLoading } = useExercises(paragraphId);
  const [filter, setFilter] = useState<DifficultyFilter>('all');

  const filteredExercises = useMemo(() => {
    if (!data?.exercises) return [];
    if (filter === 'all') return data.exercises;
    return data.exercises.filter((ex) => ex.difficulty === filter);
  }, [data?.exercises, filter]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    );
  }

  if (!data || data.total === 0) {
    return (
      <div className="card-elevated p-8 text-center">
        <BookOpen className="mx-auto h-12 w-12 text-muted-foreground/50" />
        <p className="mt-4 text-muted-foreground">{t('noExercises')}</p>
      </div>
    );
  }

  const filters: { key: DifficultyFilter; label: string }[] = [
    { key: 'all', label: t('all') },
    { key: 'A', label: 'A' },
    { key: 'B', label: 'B' },
    { key: 'C', label: 'C' },
  ];

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="text-center mb-2">
        <h2 className="text-xl font-bold text-foreground mb-1">{t('title')}</h2>
        <p className="text-sm text-muted-foreground">{t('subtitle')}</p>
      </div>

      {/* Filter pills + counts */}
      <div className="flex items-center gap-2 flex-wrap">
        {filters.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            className={`rounded-full px-4 py-1.5 text-sm font-medium transition-all ${
              filter === key
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-muted-foreground hover:bg-muted/80'
            }`}
          >
            {label}
          </button>
        ))}

        <div className="ml-auto flex gap-2 text-xs">
          {data.count_a > 0 && (
            <span className={`rounded-full px-2 py-0.5 font-medium ${difficultyColors.A}`}>
              A: {data.count_a}
            </span>
          )}
          {data.count_b > 0 && (
            <span className={`rounded-full px-2 py-0.5 font-medium ${difficultyColors.B}`}>
              B: {data.count_b}
            </span>
          )}
          {data.count_c > 0 && (
            <span className={`rounded-full px-2 py-0.5 font-medium ${difficultyColors.C}`}>
              C: {data.count_c}
            </span>
          )}
        </div>
      </div>

      {/* Exercise cards */}
      <div className="space-y-3">
        {filteredExercises.map((exercise) => {
          const contentHtml = exercise.content_html
            ? renderMathInHtml(exercise.content_html)
            : renderMathInHtml(exercise.content_text);

          return (
            <div
              key={exercise.id}
              className="rounded-lg border bg-card p-4"
            >
              {/* Exercise header */}
              <div className="flex items-center gap-2 mb-2">
                <span className="font-semibold text-foreground">
                  {exercise.exercise_number}
                </span>
                {exercise.difficulty && (
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      difficultyColors[exercise.difficulty] || 'bg-muted text-muted-foreground'
                    }`}
                  >
                    {exercise.difficulty}
                  </span>
                )}
                {exercise.is_starred && (
                  <span title={t('starred')}>
                    <Star className="h-4 w-4 text-amber-500 fill-amber-500" />
                  </span>
                )}
              </div>

              {/* Exercise content */}
              <div
                className="prose prose-sm prose-stone dark:prose-invert max-w-none
                  prose-p:text-foreground prose-p:leading-relaxed prose-p:my-1"
                dangerouslySetInnerHTML={{ __html: contentHtml }}
              />

              {/* Sub-exercises */}
              {exercise.sub_exercises && exercise.sub_exercises.length > 0 && (
                <div className="ml-6 mt-2 space-y-1">
                  {exercise.sub_exercises.map((sub, idx) => {
                    const subHtml = renderMathInHtml(sub.text);
                    return (
                      <div key={idx} className="flex gap-2 text-sm">
                        <span className="font-medium text-muted-foreground shrink-0">
                          {sub.number}
                        </span>
                        <span
                          className="text-foreground"
                          dangerouslySetInnerHTML={{ __html: subHtml }}
                        />
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
