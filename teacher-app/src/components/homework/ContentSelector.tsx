'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { Loader2 } from 'lucide-react';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useTextbooks, useChapters, useParagraphs } from '@/lib/hooks/use-content';

export interface ContentSelection {
  textbookId?: number;
  textbookTitle?: string;
  subject?: string;
  gradeLevel?: number;
  chapterId?: number;
  chapterNumber?: number;
  chapterTitle?: string;
  paragraphId?: number;
  paragraphNumber?: number;
  paragraphTitle?: string;
}

interface ContentSelectorProps {
  onSelect: (selection: ContentSelection) => void;
  disabled?: boolean;
}

export function ContentSelector({ onSelect, disabled }: ContentSelectorProps) {
  const t = useTranslations('homework.task');

  const [selectedTextbookId, setSelectedTextbookId] = useState<number | null>(null);
  const [selectedChapterId, setSelectedChapterId] = useState<number | null>(null);
  const [selectedParagraphId, setSelectedParagraphId] = useState<number | null>(null);

  const { data: textbooks, isLoading: textbooksLoading } = useTextbooks();
  const { data: chapters, isLoading: chaptersLoading } = useChapters(selectedTextbookId || 0);
  const { data: paragraphs, isLoading: paragraphsLoading } = useParagraphs(selectedChapterId || 0);

  // Reset chapter when textbook changes
  useEffect(() => {
    setSelectedChapterId(null);
    setSelectedParagraphId(null);
  }, [selectedTextbookId]);

  // Reset paragraph when chapter changes
  useEffect(() => {
    setSelectedParagraphId(null);
  }, [selectedChapterId]);

  // Notify parent when selection changes
  // NOTE: onSelect intentionally excluded from deps to prevent infinite loop
  // when parent passes inline function. The callback identity doesn't affect
  // when we should notify - only the selected IDs matter.
  useEffect(() => {
    const selectedTextbook = textbooks?.find((tb) => tb.id === selectedTextbookId);
    const selectedChapter = chapters?.find((ch) => ch.id === selectedChapterId);
    const selectedParagraph = paragraphs?.find((p) => p.id === selectedParagraphId);

    const selection: ContentSelection = {};

    if (selectedTextbook) {
      selection.textbookId = selectedTextbook.id;
      selection.textbookTitle = selectedTextbook.title;
      selection.subject = selectedTextbook.subject;
      selection.gradeLevel = selectedTextbook.grade_level;
    }

    if (selectedChapter) {
      selection.chapterId = selectedChapter.id;
      selection.chapterNumber = selectedChapter.number;
      selection.chapterTitle = selectedChapter.title;
    }

    if (selectedParagraph) {
      selection.paragraphId = selectedParagraph.id;
      selection.paragraphNumber = selectedParagraph.number;
      selection.paragraphTitle = selectedParagraph.title;
    }

    // Only notify if at least chapter or paragraph is selected
    if (selectedParagraphId || selectedChapterId) {
      onSelect(selection);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedParagraphId, selectedChapterId, selectedTextbookId, textbooks, chapters, paragraphs]);

  return (
    <div className="space-y-4">
      {/* Textbook Select */}
      <div className="space-y-2">
        <Label>{t('textbook')}</Label>
        <Select
          value={selectedTextbookId?.toString() || ''}
          onValueChange={(v) => setSelectedTextbookId(Number(v))}
          disabled={disabled || textbooksLoading}
        >
          <SelectTrigger>
            {textbooksLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <SelectValue placeholder={t('selectTextbook')} />
            )}
          </SelectTrigger>
          <SelectContent>
            {textbooks?.map((tb) => (
              <SelectItem key={tb.id} value={tb.id.toString()}>
                {tb.title} ({tb.grade_level} класс)
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Chapter Select */}
      <div className="space-y-2">
        <Label>{t('chapter')}</Label>
        <Select
          value={selectedChapterId?.toString() || ''}
          onValueChange={(v) => setSelectedChapterId(Number(v))}
          disabled={disabled || !selectedTextbookId || chaptersLoading}
        >
          <SelectTrigger>
            {chaptersLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <SelectValue placeholder={t('selectChapter')} />
            )}
          </SelectTrigger>
          <SelectContent>
            {chapters?.map((ch) => (
              <SelectItem key={ch.id} value={ch.id.toString()}>
                {ch.number}. {ch.title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Paragraph Select */}
      <div className="space-y-2">
        <Label>{t('paragraph')}</Label>
        <Select
          value={selectedParagraphId?.toString() || ''}
          onValueChange={(v) => setSelectedParagraphId(Number(v))}
          disabled={disabled || !selectedChapterId || paragraphsLoading}
        >
          <SelectTrigger>
            {paragraphsLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <SelectValue placeholder={t('selectParagraph')} />
            )}
          </SelectTrigger>
          <SelectContent>
            {paragraphs?.map((p) => (
              <SelectItem key={p.id} value={p.id.toString()}>
                §{p.number}. {p.title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
