'use client';

import { useState, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import {
  CheckCircle2,
  ChevronRight,
  ChevronLeft,
  BookOpen,
  Code2,
  Loader2,
} from 'lucide-react';
import type { LessonDetail as LessonDetailType } from '@/lib/api/coding';
import { useCompleteLesson } from '@/lib/hooks/use-coding';
import dynamic from 'next/dynamic';

const ChallengeRunner = dynamic(
  () =>
    import('@/components/sandbox/ChallengeRunner').then((m) => ({
      default: m.ChallengeRunner,
    })),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    ),
  }
);

interface LessonViewProps {
  lesson: LessonDetailType;
  courseSlug: string;
  onNext?: () => void;
  onPrev?: () => void;
  hasNext: boolean;
  hasPrev: boolean;
  lessonNumber: number;
  totalLessons: number;
}

export function LessonView({
  lesson,
  courseSlug,
  onNext,
  onPrev,
  hasNext,
  hasPrev,
  lessonNumber,
  totalLessons,
}: LessonViewProps) {
  const t = useTranslations('courses');
  const [activeTab, setActiveTab] = useState<'theory' | 'practice'>('theory');
  const completeMutation = useCompleteLesson(lesson.id, courseSlug);

  const handleComplete = useCallback(async () => {
    if (!lesson.is_completed) {
      await completeMutation.mutateAsync();
    }
    if (hasNext && onNext) {
      onNext();
    }
  }, [lesson.is_completed, completeMutation, hasNext, onNext]);

  return (
    <div className="flex flex-col h-full">
      {/* Tab bar (only show if challenge exists) */}
      {lesson.challenge && (
        <div className="flex border-b border-border px-4">
          <button
            onClick={() => setActiveTab('theory')}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'theory'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <BookOpen className="h-4 w-4" />
            {t('theory')}
          </button>
          <button
            onClick={() => setActiveTab('practice')}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'practice'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <Code2 className="h-4 w-4" />
            {t('practice')}
          </button>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 min-h-0 overflow-y-auto">
        {activeTab === 'theory' ? (
          <div className="max-w-3xl mx-auto px-4 py-6">
            {/* Theory content (markdown-like) */}
            <div
              className="prose prose-sm dark:prose-invert max-w-none
                prose-headings:text-foreground prose-p:text-foreground/80
                prose-code:bg-muted prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded
                prose-pre:bg-muted prose-pre:border prose-pre:border-border"
              dangerouslySetInnerHTML={{ __html: formatTheory(lesson.theory_content) }}
            />

            {/* Complete + navigation */}
            <div className="flex items-center justify-between mt-8 pt-6 border-t border-border">
              <button
                onClick={onPrev}
                disabled={!hasPrev}
                className="flex items-center gap-1 px-4 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:bg-muted transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="h-4 w-4" />
                {t('prevLesson')}
              </button>

              <div className="text-xs text-muted-foreground">
                {lessonNumber} / {totalLessons}
              </div>

              {lesson.is_completed ? (
                hasNext ? (
                  <button
                    onClick={onNext}
                    className="flex items-center gap-1 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
                  >
                    {t('nextLesson')}
                    <ChevronRight className="h-4 w-4" />
                  </button>
                ) : (
                  <div className="flex items-center gap-1 text-sm text-green-500 font-medium">
                    <CheckCircle2 className="h-4 w-4" />
                    {t('completed')}
                  </div>
                )
              ) : (
                <button
                  onClick={handleComplete}
                  disabled={completeMutation.isPending}
                  className="flex items-center gap-1 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
                >
                  {completeMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : lesson.challenge ? (
                    <>
                      {t('markRead')}
                      <ChevronRight className="h-4 w-4" />
                    </>
                  ) : (
                    <>
                      {t('completeAndNext')}
                      <ChevronRight className="h-4 w-4" />
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        ) : (
          /* Practice tab — challenge runner */
          lesson.challenge && (
            <div className="h-full p-3">
              <ChallengeRunner challenge={lesson.challenge} />
            </div>
          )
        )}
      </div>
    </div>
  );
}

/**
 * Simple markdown-to-html conversion for theory content.
 * Handles: headers, code blocks, bold, inline code, paragraphs.
 */
function formatTheory(text: string): string {
  return text
    // Code blocks (```python ... ```)
    .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>')
    // Headers
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    // Bold
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // Inline code
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    // Line breaks → paragraphs (double newline)
    .replace(/\n\n/g, '</p><p>')
    // Single newlines within paragraphs
    .replace(/\n/g, '<br/>')
    // Wrap in paragraph
    .replace(/^/, '<p>')
    .replace(/$/, '</p>');
}
