'use client';

import { Link } from '@/i18n/routing';
import { StudentParagraph } from '@/lib/api/textbooks';
import { useTranslations } from 'next-intl';
import {
  CheckCircle2,
  Circle,
  PlayCircle,
  ChevronLeft,
  ChevronRight,
  List,
  X,
} from 'lucide-react';
import { useState } from 'react';

interface ChapterSidebarProps {
  paragraphs: StudentParagraph[];
  currentParagraphId: number;
  chapterTitle: string;
  chapterNumber: number;
  chapterId: number;
}

export function ChapterSidebar({
  paragraphs,
  currentParagraphId,
  chapterTitle,
  chapterNumber,
  chapterId,
}: ChapterSidebarProps) {
  const t = useTranslations('paragraph');
  const tCommon = useTranslations('common');
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Calculate progress
  const completedCount = paragraphs.filter((p) => p.status === 'completed').length;
  const progressPercent = paragraphs.length > 0
    ? Math.round((completedCount / paragraphs.length) * 100)
    : 0;

  return (
    <>
      {/* Desktop Sidebar */}
      <aside
        className={`hidden lg:flex flex-col border-r border-border bg-background/50 transition-all duration-300 ${
          isCollapsed ? 'w-12' : 'w-72'
        }`}
      >
        {/* Collapse toggle */}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="flex items-center justify-center h-12 border-b border-border hover:bg-muted transition-colors"
          title={isCollapsed ? t('sidebar.expand') : t('sidebar.collapse')}
        >
          {isCollapsed ? (
            <ChevronRight className="h-5 w-5 text-muted-foreground" />
          ) : (
            <ChevronLeft className="h-5 w-5 text-muted-foreground" />
          )}
        </button>

        {!isCollapsed && (
          <>
            {/* Chapter Header */}
            <div className="p-4 border-b border-border">
              <h2 className="font-semibold text-foreground line-clamp-2">
                {t('chapterShort', { number: chapterNumber })}. {chapterTitle}
              </h2>

              {/* Progress */}
              <div className="mt-3">
                <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
                  <span>{t('sidebar.progress')}</span>
                  <span>{completedCount}/{paragraphs.length}</span>
                </div>
                <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-success rounded-full transition-all"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Paragraphs List */}
            <nav className="flex-1 overflow-y-auto py-2">
              <ul className="space-y-0.5">
                {paragraphs.map((paragraph) => {
                  const isCurrent = paragraph.id === currentParagraphId;
                  const isCompleted = paragraph.status === 'completed';
                  const isInProgress = paragraph.status === 'in_progress';

                  return (
                    <li key={paragraph.id}>
                      <Link
                        href={`/paragraphs/${paragraph.id}`}
                        className={`flex items-start gap-3 px-4 py-2.5 transition-all group ${
                          isCurrent
                            ? 'bg-primary/10 border-l-2 border-l-primary'
                            : 'hover:bg-muted border-l-2 border-l-transparent'
                        }`}
                      >
                        {/* Status Icon */}
                        <div className="flex-shrink-0 mt-0.5">
                          {isCompleted ? (
                            <CheckCircle2 className="h-5 w-5 text-success" />
                          ) : isInProgress ? (
                            <PlayCircle className="h-5 w-5 text-primary" />
                          ) : (
                            <Circle className={`h-5 w-5 ${isCurrent ? 'text-primary' : 'text-muted-foreground/50'}`} />
                          )}
                        </div>

                        {/* Paragraph Info */}
                        <div className="flex-1 min-w-0">
                          <p
                            className={`text-sm font-medium line-clamp-2 ${
                              isCurrent
                                ? 'text-primary'
                                : isCompleted
                                ? 'text-muted-foreground'
                                : 'text-foreground group-hover:text-primary'
                            }`}
                          >
                            {paragraph.title || `${t('sidebar.paragraph')} ${paragraph.number}`}
                          </p>

                          {/* Status hint for current */}
                          {isCurrent && !isCompleted && (
                            <p className="text-xs text-muted-foreground mt-0.5">
                              {t('sidebar.currentlyViewing')}
                            </p>
                          )}
                        </div>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </nav>
          </>
        )}

        {/* Collapsed state - show icons only */}
        {isCollapsed && (
          <nav className="flex-1 overflow-y-auto py-2">
            <ul className="space-y-1">
              {paragraphs.map((paragraph) => {
                const isCurrent = paragraph.id === currentParagraphId;
                const isCompleted = paragraph.status === 'completed';
                const isInProgress = paragraph.status === 'in_progress';

                return (
                  <li key={paragraph.id}>
                    <Link
                      href={`/paragraphs/${paragraph.id}`}
                      className={`flex items-center justify-center py-2 transition-all ${
                        isCurrent
                          ? 'bg-primary/10 border-l-2 border-l-primary'
                          : 'hover:bg-muted border-l-2 border-l-transparent'
                      }`}
                      title={paragraph.title || `§${paragraph.number}`}
                    >
                      {isCompleted ? (
                        <CheckCircle2 className="h-5 w-5 text-success" />
                      ) : isInProgress ? (
                        <PlayCircle className="h-5 w-5 text-primary" />
                      ) : (
                        <Circle className={`h-5 w-5 ${isCurrent ? 'text-primary' : 'text-muted-foreground/50'}`} />
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>
        )}
      </aside>
    </>
  );
}

// Mobile Sidebar Trigger Button
interface MobileSidebarTriggerProps {
  onClick: () => void;
  paragraphsCount: number;
  completedCount: number;
}

export function MobileSidebarTrigger({ onClick, paragraphsCount, completedCount }: MobileSidebarTriggerProps) {
  const t = useTranslations('paragraph');

  return (
    <button
      onClick={onClick}
      className="lg:hidden flex items-center gap-2 px-3 py-1.5 rounded-full bg-muted text-sm font-medium text-muted-foreground hover:bg-muted/80 transition-colors"
    >
      <List className="h-4 w-4" />
      <span>{completedCount}/{paragraphsCount}</span>
    </button>
  );
}

// Mobile Sidebar Sheet
interface MobileSidebarSheetProps {
  isOpen: boolean;
  onClose: () => void;
  paragraphs: StudentParagraph[];
  currentParagraphId: number;
  chapterTitle: string;
  chapterNumber: number;
  chapterId: number;
}

export function MobileSidebarSheet({
  isOpen,
  onClose,
  paragraphs,
  currentParagraphId,
  chapterTitle,
  chapterNumber,
  chapterId,
}: MobileSidebarSheetProps) {
  const t = useTranslations('paragraph');

  // Calculate progress
  const completedCount = paragraphs.filter((p) => p.status === 'completed').length;
  const progressPercent = paragraphs.length > 0
    ? Math.round((completedCount / paragraphs.length) * 100)
    : 0;

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-50 bg-black/50 lg:hidden"
        onClick={onClose}
      />

      {/* Sheet */}
      <div className="fixed inset-y-0 left-0 z-50 w-80 max-w-[85vw] bg-background shadow-xl lg:hidden animate-in slide-in-from-left duration-300">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <h2 className="font-semibold text-foreground">{t('sidebar.contents')}</h2>
          <button
            onClick={onClose}
            className="p-2 rounded-full hover:bg-muted transition-colors"
          >
            <X className="h-5 w-5 text-muted-foreground" />
          </button>
        </div>

        {/* Chapter Info */}
        <div className="p-4 border-b border-border bg-muted/30">
          <h3 className="font-medium text-foreground line-clamp-2">
            {t('chapterShort', { number: chapterNumber })}. {chapterTitle}
          </h3>

          {/* Progress */}
          <div className="mt-3">
            <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
              <span>{t('sidebar.progress')}</span>
              <span>{completedCount}/{paragraphs.length}</span>
            </div>
            <div className="h-1.5 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-success rounded-full transition-all"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>
        </div>

        {/* Paragraphs List */}
        <nav className="flex-1 overflow-y-auto py-2 max-h-[calc(100vh-200px)]">
          <ul className="space-y-0.5">
            {paragraphs.map((paragraph) => {
              const isCurrent = paragraph.id === currentParagraphId;
              const isCompleted = paragraph.status === 'completed';
              const isInProgress = paragraph.status === 'in_progress';

              return (
                <li key={paragraph.id}>
                  <Link
                    href={`/paragraphs/${paragraph.id}`}
                    onClick={onClose}
                    className={`flex items-start gap-3 px-4 py-3 transition-all ${
                      isCurrent
                        ? 'bg-primary/10 border-l-4 border-l-primary'
                        : 'hover:bg-muted border-l-4 border-l-transparent'
                    }`}
                  >
                    {/* Status Icon */}
                    <div className="flex-shrink-0 mt-0.5">
                      {isCompleted ? (
                        <CheckCircle2 className="h-5 w-5 text-success" />
                      ) : isInProgress ? (
                        <PlayCircle className="h-5 w-5 text-primary" />
                      ) : (
                        <Circle className={`h-5 w-5 ${isCurrent ? 'text-primary' : 'text-muted-foreground/50'}`} />
                      )}
                    </div>

                    {/* Paragraph Info */}
                    <div className="flex-1 min-w-0">
                      <p
                        className={`text-sm font-medium ${
                          isCurrent
                            ? 'text-primary'
                            : isCompleted
                            ? 'text-muted-foreground'
                            : 'text-foreground'
                        }`}
                      >
                        {paragraph.title || `${t('sidebar.paragraph')} ${paragraph.number}`}
                      </p>

                      {isCurrent && !isCompleted && (
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {t('sidebar.currentlyViewing')}
                        </p>
                      )}
                    </div>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </div>
    </>
  );
}
