'use client';

import { useMemo, useState, useCallback, useRef, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import {
  BookOpen,
  Headphones,
  Layers,
  Target,
  Key,
  Brain,
  Dumbbell,
  Sparkles,
} from 'lucide-react';
import { AudioPlayer } from './AudioPlayer';
import { FlashCards } from './FlashCards';
import ExerciseList from '@/components/learning/ExerciseList';
import { renderMathInHtml } from '@/components/common/MathText';
import type { ParagraphDetail, ParagraphRichContent, ParagraphProgress } from '@/lib/api/textbooks';

type ContentTab = 'text' | 'audio' | 'cards' | 'practice' | 'exercises';

interface ParagraphContentProps {
  paragraph: ParagraphDetail;
  richContent?: ParagraphRichContent | null;
  progress?: ParagraphProgress | null;
  embeddedQuestions?: Array<unknown> | null;
  exercisesData?: { total: number } | null;
  paragraphId: number;
  getMediaUrl: (url?: string | null) => string | null;
  practiceContent?: React.ReactNode;
  quizContent?: React.ReactNode;
  activeTab?: ContentTab;
  onTabChange?: (tab: ContentTab) => void;
  onExplainSelection?: (selectedText: string) => void;
}

export function ParagraphContent({
  paragraph,
  richContent,
  progress,
  embeddedQuestions,
  exercisesData,
  paragraphId,
  getMediaUrl,
  practiceContent,
  quizContent,
  activeTab: controlledTab,
  onTabChange,
  onExplainSelection,
}: ParagraphContentProps) {
  const t = useTranslations('paragraph');
  const [internalTab, setInternalTab] = useState<ContentTab>('text');
  const activeTab = controlledTab ?? internalTab;
  const setActiveTab = onTabChange ?? setInternalTab;

  // Text selection tooltip
  const contentRef = useRef<HTMLDivElement>(null);
  const [selectionTooltip, setSelectionTooltip] = useState<{
    text: string;
    top: number;
    left: number;
  } | null>(null);

  const handleMouseUp = useCallback(() => {
    if (!onExplainSelection) return;

    const selection = window.getSelection();
    const text = selection?.toString().trim();

    if (!text || text.length < 3) {
      setSelectionTooltip(null);
      return;
    }

    const range = selection?.getRangeAt(0);
    if (!range || !contentRef.current) return;

    // Check selection is inside our content div
    if (!contentRef.current.contains(range.commonAncestorContainer)) {
      setSelectionTooltip(null);
      return;
    }

    const rect = range.getBoundingClientRect();
    const containerRect = contentRef.current.getBoundingClientRect();

    setSelectionTooltip({
      text,
      top: rect.top - containerRect.top - 44,
      left: Math.min(
        Math.max(rect.left - containerRect.left + rect.width / 2 - 60, 0),
        containerRect.width - 120
      ),
    });
  }, [onExplainSelection]);

  // Hide tooltip on scroll or click outside
  useEffect(() => {
    const handleScroll = () => setSelectionTooltip(null);
    const handleMouseDown = (e: MouseEvent) => {
      if (!(e.target as HTMLElement)?.closest('[data-explain-tooltip]')) {
        setSelectionTooltip(null);
      }
    };
    const container = contentRef.current?.closest('.overflow-y-auto');
    container?.addEventListener('scroll', handleScroll);
    document.addEventListener('mousedown', handleMouseDown);
    return () => {
      container?.removeEventListener('scroll', handleScroll);
      document.removeEventListener('mousedown', handleMouseDown);
    };
  }, []);

  // Available tabs
  const availableTabs = useMemo(() => {
    const tabs: ContentTab[] = ['text'];
    if (richContent?.has_audio || paragraph?.has_audio) tabs.push('audio');
    if (richContent?.has_cards || paragraph?.has_cards) tabs.push('cards');
    if (embeddedQuestions && embeddedQuestions.length > 0) tabs.push('practice');
    if (exercisesData && exercisesData.total > 0) tabs.push('exercises');
    return tabs;
  }, [richContent, paragraph, embeddedQuestions, exercisesData]);

  // Process content with KaTeX
  const displayContent = useMemo(() => {
    const raw = richContent?.explain_text || paragraph?.content || null;
    if (!raw) return null;
    return renderMathInHtml(raw);
  }, [richContent, paragraph]);

  return (
    <div>
      {/* Learning Objective */}
      {paragraph.learning_objective && (
        <section className="mb-6 card-flat border-l-4 border-l-primary p-4">
          <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-primary/10">
              <Target className="h-4 w-4 text-primary" />
            </div>
            <div>
              <h2 className="font-semibold text-foreground mb-1">{t('learningObjective')}</h2>
              <p className="text-sm text-muted-foreground">{paragraph.learning_objective}</p>
            </div>
          </div>
        </section>
      )}

      {/* Key Terms */}
      {paragraph.key_terms && paragraph.key_terms.length > 0 && (
        <section className="mb-6">
          <div className="flex items-center gap-2 mb-3">
            <Key className="h-4 w-4 text-primary" />
            <h2 className="font-semibold text-foreground">{t('keyTerms')}</h2>
          </div>
          <div className="flex flex-wrap gap-2">
            {paragraph.key_terms.map((term, index) => (
              <span
                key={index}
                className="rounded-full bg-primary/10 px-3 py-1 text-sm font-medium text-primary"
              >
                {term}
              </span>
            ))}
          </div>
        </section>
      )}

      {/* Content Tabs */}
      {availableTabs.length > 1 && (
        <div className="mb-4 flex gap-2 overflow-x-auto pb-2">
          {availableTabs.map((tab) => {
            const TabIcon = tab === 'text' ? BookOpen : tab === 'audio' ? Headphones : tab === 'practice' ? Brain : tab === 'exercises' ? Dumbbell : Layers;
            const tabLabel = tab === 'practice' ? t('steps.practice') : tab === 'exercises' ? t('tabs.exercises') : t(`tabs.${tab}`);
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-all ${
                  activeTab === tab
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:bg-muted/80'
                }`}
              >
                <TabIcon className="h-4 w-4" />
                {tabLabel}
                {tab === 'practice' && progress && progress.embedded_questions_total > 0 && (
                  <span className="ml-1 px-1.5 py-0.5 text-xs rounded-full bg-white/20">
                    {progress.embedded_questions_answered}/{progress.embedded_questions_total}
                  </span>
                )}
                {tab === 'exercises' && exercisesData && (
                  <span className="ml-1 px-1.5 py-0.5 text-xs rounded-full bg-white/20">
                    {exercisesData.total}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}

      {/* Content Area */}
      <main className="mb-8">
        {activeTab === 'text' && (
          <article className="card-elevated p-6">
            {displayContent ? (
              <div ref={contentRef} className="relative" onMouseUp={handleMouseUp}>
                {/* Selection tooltip */}
                {selectionTooltip && onExplainSelection && (
                  <div
                    data-explain-tooltip
                    className="absolute z-50 animate-in fade-in slide-in-from-bottom-1 duration-150"
                    style={{ top: selectionTooltip.top, left: selectionTooltip.left }}
                  >
                    <button
                      onMouseDown={(e) => e.preventDefault()}
                      onMouseUp={(e) => e.stopPropagation()}
                      onClick={() => {
                        onExplainSelection(selectionTooltip.text);
                        setSelectionTooltip(null);
                        window.getSelection()?.removeAllRanges();
                      }}
                      className="flex items-center gap-1.5 px-3 py-2 bg-success text-white text-xs font-medium rounded-lg shadow-lg hover:bg-success/90 transition-colors whitespace-nowrap"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      {t('explainSelection')}
                    </button>
                  </div>
                )}
                <div
                  className="prose prose-stone dark:prose-invert max-w-none
                    prose-headings:text-foreground prose-headings:font-bold
                    prose-p:text-foreground prose-p:leading-relaxed
                    prose-strong:text-foreground prose-strong:font-semibold
                    prose-ul:text-foreground prose-ol:text-foreground
                    prose-li:marker:text-primary"
                  dangerouslySetInnerHTML={{ __html: displayContent }}
                />
              </div>
            ) : (
              <div className="text-center py-8">
                <BookOpen className="mx-auto h-12 w-12 text-muted-foreground/50" />
                <p className="mt-4 text-muted-foreground">{t('noContent')}</p>
              </div>
            )}
          </article>
        )}

        {activeTab === 'audio' && (
          <AudioPlayer audioUrl={getMediaUrl(richContent?.audio_url)} t={t} />
        )}

        {activeTab === 'cards' && (
          <FlashCards cards={richContent?.cards || []} t={t} />
        )}

        {activeTab === 'practice' && practiceContent}

        {activeTab === 'exercises' && paragraphId && (
          <ExerciseList paragraphId={paragraphId} />
        )}
      </main>

      {/* Quiz below content */}
      {quizContent}
    </div>
  );
}
