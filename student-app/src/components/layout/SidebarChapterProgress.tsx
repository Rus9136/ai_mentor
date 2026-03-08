'use client';

import { Link } from '@/i18n/routing';
import { useTranslations } from 'next-intl';
import { StudentParagraph } from '@/lib/api/textbooks';

interface SidebarChapterProgressProps {
  paragraphs: StudentParagraph[];
  currentParagraphId: number;
  chapterTitle: string;
  chapterNumber: number;
  chapterId: number;
  textbookTitle?: string;
}

export function SidebarChapterProgress({
  paragraphs,
  currentParagraphId,
  chapterTitle,
  chapterNumber,
  chapterId,
  textbookTitle,
}: SidebarChapterProgressProps) {
  const t = useTranslations('paragraph');

  const completedCount = paragraphs.filter((p) => p.status === 'completed').length;
  const progressPercent = paragraphs.length > 0
    ? Math.round((completedCount / paragraphs.length) * 100)
    : 0;

  return (
    <div className="flex flex-col h-full">
      {/* Chapter Header */}
      <div className="px-[10px] pt-3 pb-2">
        <div className="px-[10px] mb-1.5 text-[10px] font-bold text-[#A09080] uppercase tracking-[1px] truncate">
          {textbookTitle ? `${textbookTitle} · ${t('chapterShort', { number: chapterNumber })}` : t('chapterShort', { number: chapterNumber })}
        </div>

        {/* Progress */}
        <div className="px-[10px] mb-3">
          <div className="text-[11px] font-semibold text-[#A09080] mb-1.5">
            {t('sidebar.progress')}: {completedCount} / {paragraphs.length}
          </div>
          <div className="h-[5px] bg-[#EDE8E3] rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary to-primary/70 rounded-full transition-all duration-400"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* Paragraphs List */}
      <nav className="flex-1 overflow-y-auto px-[10px] pb-4">
        <ul className="space-y-0.5">
          {paragraphs.map((paragraph) => {
            const isCurrent = paragraph.id === currentParagraphId;
            const isCompleted = paragraph.status === 'completed';

            return (
              <li key={paragraph.id}>
                <Link
                  href={`/paragraphs/${paragraph.id}`}
                  className={`flex items-start gap-2 px-[10px] py-[7px] rounded-[8px] text-xs font-semibold transition-all ${
                    isCurrent
                      ? 'bg-[#FEF0E3] text-primary'
                      : 'text-[#6B5B4E] hover:bg-[#F0E8E0]'
                  }`}
                >
                  {/* Status dot */}
                  <div
                    className={`w-4 h-4 rounded-full border-2 flex-shrink-0 mt-0.5 transition-all ${
                      isCompleted
                        ? 'bg-success border-success'
                        : isCurrent
                        ? 'bg-primary border-primary'
                        : 'border-[#D0C8C0]'
                    }`}
                  />
                  <span className="line-clamp-2">
                    {paragraph.title || `§${paragraph.number}`}
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Back to chapter */}
      <div className="px-4 py-3 border-t border-[#EDE8E3]">
        <Link
          href={`/chapters/${chapterId}`}
          className="text-xs font-semibold text-[#A09080] hover:text-primary transition-colors"
        >
          {t('sidebar.backToChapter')}
        </Link>
      </div>
    </div>
  );
}
