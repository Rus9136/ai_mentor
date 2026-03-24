'use client';

import { useState, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { useRouter } from '@/i18n/routing';
import { Button } from '@/components/ui/button';
import { Loader2, Plus, X, GripVertical } from 'lucide-react';
import { useCreateFactile } from '@/lib/hooks/use-quiz';
import { useChapterQuestions } from '@/lib/hooks/use-quiz';
import { getTextbooks, getChapters } from '@/lib/api/content';
import { useQuery } from '@tanstack/react-query';
import { useClasses } from '@/lib/hooks/use-teacher-data';
import { Checkbox } from '@/components/ui/checkbox';
import type { ParagraphQuestions, QuestionPreview } from '@/lib/api/quiz';

interface Category {
  name: string;
  questionIds: number[];
}

export default function FactileCreateForm() {
  const t = useTranslations('quiz');
  const router = useRouter();

  // Content selection
  const [classId, setClassId] = useState<number | undefined>();
  const [textbookId, setTextbookId] = useState<number | undefined>();
  const [chapterId, setChapterId] = useState<number | undefined>();

  // Categories
  const [categories, setCategories] = useState<Category[]>([
    { name: '', questionIds: [] },
    { name: '', questionIds: [] },
  ]);
  const [pointValues, setPointValues] = useState([100, 200, 300, 400, 500]);

  // Which category is being edited (question picker)
  const [editingCatIdx, setEditingCatIdx] = useState<number | null>(null);

  const { data: classes } = useClasses();
  const { data: textbooks } = useQuery({ queryKey: ['textbooks'], queryFn: getTextbooks });
  const { data: chapters } = useQuery({
    queryKey: ['chapters', textbookId],
    queryFn: () => getChapters(textbookId!),
    enabled: !!textbookId,
  });
  const { data: paragraphs, isLoading: loadingQuestions } = useChapterQuestions(chapterId);

  const createFactile = useCreateFactile();

  const totalQuestions = categories.reduce((sum, cat) => sum + cat.questionIds.length, 0);
  const maxPerCategory = Math.max(...categories.map(c => c.questionIds.length), 0);
  const canCreate = categories.length >= 2
    && categories.every(c => c.name.trim() && c.questionIds.length > 0)
    && totalQuestions >= 4;

  const handleCreate = async () => {
    if (!canCreate) return;
    try {
      const result = await createFactile.mutateAsync({
        class_id: classId,
        categories: categories.map(c => ({
          name: c.name.trim(),
          question_ids: c.questionIds,
        })),
        point_values: pointValues.slice(0, maxPerCategory),
      });
      router.push(`/quiz/${result.id}`);
    } catch (err) {
      console.error('Failed to create factile:', err);
    }
  };

  const addCategory = () => {
    if (categories.length >= 6) return;
    setCategories([...categories, { name: '', questionIds: [] }]);
  };

  const removeCategory = (idx: number) => {
    if (categories.length <= 2) return;
    setCategories(categories.filter((_, i) => i !== idx));
    if (editingCatIdx === idx) setEditingCatIdx(null);
  };

  const updateCategoryName = (idx: number, name: string) => {
    const updated = [...categories];
    updated[idx] = { ...updated[idx], name };
    setCategories(updated);
  };

  const toggleQuestion = useCallback((catIdx: number, questionId: number) => {
    setCategories(prev => {
      const updated = [...prev];
      const cat = { ...updated[catIdx] };
      if (cat.questionIds.includes(questionId)) {
        cat.questionIds = cat.questionIds.filter(id => id !== questionId);
      } else {
        if (cat.questionIds.length >= 5) return prev; // max 5 per category
        cat.questionIds = [...cat.questionIds, questionId];
      }
      updated[catIdx] = cat;
      return updated;
    });
  }, []);

  // All questions already used in other categories
  const usedQuestionIds = new Set(
    categories.flatMap((cat, i) => i !== editingCatIdx ? cat.questionIds : [])
  );

  return (
    <div className="space-y-6">
      {/* Content selection */}
      <div className="rounded-xl border bg-card p-4 space-y-4">
        <h3 className="font-semibold">{t('selectContent')}</h3>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* Class */}
          <select
            value={classId || ''}
            onChange={(e) => setClassId(e.target.value ? Number(e.target.value) : undefined)}
            className="rounded-lg border bg-background px-3 py-2 text-sm"
          >
            <option value="">{t('selectClass')}</option>
            {(classes || []).map((c: { id: number; name: string }) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>

          {/* Textbook */}
          <select
            value={textbookId || ''}
            onChange={(e) => {
              setTextbookId(e.target.value ? Number(e.target.value) : undefined);
              setChapterId(undefined);
            }}
            className="rounded-lg border bg-background px-3 py-2 text-sm"
          >
            <option value="">{t('selectTextbook')}</option>
            {(textbooks || []).map((tb: { id: number; title: string }) => (
              <option key={tb.id} value={tb.id}>{tb.title}</option>
            ))}
          </select>

          {/* Chapter */}
          <select
            value={chapterId || ''}
            onChange={(e) => setChapterId(e.target.value ? Number(e.target.value) : undefined)}
            className="rounded-lg border bg-background px-3 py-2 text-sm"
            disabled={!textbookId}
          >
            <option value="">{t('selectChapter')}</option>
            {(chapters || []).map((ch: { id: number; title: string; number: number }) => (
              <option key={ch.id} value={ch.id}>{ch.number}. {ch.title}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Categories */}
      <div className="rounded-xl border bg-card p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">{t('factileCategories')}</h3>
          {categories.length < 6 && (
            <Button variant="outline" size="sm" onClick={addCategory} className="gap-1">
              <Plus className="h-3 w-3" /> {t('factileAddCategory')}
            </Button>
          )}
        </div>

        {categories.map((cat, catIdx) => (
          <div key={catIdx} className="rounded-lg border p-3 space-y-2">
            <div className="flex items-center gap-2">
              <GripVertical className="h-4 w-4 text-muted-foreground shrink-0" />
              <input
                type="text"
                value={cat.name}
                onChange={(e) => updateCategoryName(catIdx, e.target.value)}
                placeholder={`${t('factileCategoryName')} ${catIdx + 1}`}
                className="flex-1 rounded-md border bg-background px-3 py-1.5 text-sm"
              />
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setEditingCatIdx(editingCatIdx === catIdx ? null : catIdx)}
                className="text-xs"
              >
                {cat.questionIds.length > 0
                  ? `${cat.questionIds.length} ${t('factileQuestionsSelected')}`
                  : t('factilePickQuestions')
                }
              </Button>
              {categories.length > 2 && (
                <button onClick={() => removeCategory(catIdx)} className="p-1 hover:bg-muted rounded">
                  <X className="h-4 w-4 text-muted-foreground" />
                </button>
              )}
            </div>

            {/* Inline question picker for this category */}
            {editingCatIdx === catIdx && (
              <div className="mt-2 ml-6 max-h-60 overflow-y-auto border rounded-lg p-2 bg-muted/30">
                {!chapterId ? (
                  <p className="text-sm text-muted-foreground p-2">{t('factileSelectChapterFirst')}</p>
                ) : loadingQuestions ? (
                  <div className="flex justify-center py-4">
                    <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                  </div>
                ) : (
                  (paragraphs || []).map((para: ParagraphQuestions) => (
                    <div key={para.paragraph_id} className="mb-2">
                      <p className="text-xs font-medium text-muted-foreground mb-1">
                        §{para.paragraph_number} {para.paragraph_title}
                      </p>
                      {para.questions
                        .filter(q => q.question_type === 'single_choice')
                        .map((q: QuestionPreview) => {
                          const isInThisCat = cat.questionIds.includes(q.id);
                          const isUsedElsewhere = usedQuestionIds.has(q.id);
                          return (
                            <label
                              key={q.id}
                              className={`flex items-start gap-2 py-1 px-2 rounded text-sm cursor-pointer hover:bg-muted ${
                                isUsedElsewhere && !isInThisCat ? 'opacity-40' : ''
                              }`}
                            >
                              <Checkbox
                                checked={isInThisCat}
                                onCheckedChange={() => toggleQuestion(catIdx, q.id)}
                                disabled={isUsedElsewhere && !isInThisCat}
                                className="mt-0.5"
                              />
                              <span className="line-clamp-2">{q.question_text}</span>
                            </label>
                          );
                        })}
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Point values */}
      <div className="rounded-xl border bg-card p-4 space-y-3">
        <h3 className="font-semibold">{t('factilePointValues')}</h3>
        <div className="flex gap-2">
          {pointValues.map((val, i) => (
            <input
              key={i}
              type="number"
              value={val}
              onChange={(e) => {
                const updated = [...pointValues];
                updated[i] = Math.max(0, parseInt(e.target.value) || 0);
                setPointValues(updated);
              }}
              className="w-20 rounded-md border bg-background px-2 py-1.5 text-center text-sm font-bold"
            />
          ))}
        </div>
        <p className="text-xs text-muted-foreground">{t('factilePointValuesHint')}</p>
      </div>

      {/* Create button */}
      <Button
        onClick={handleCreate}
        disabled={!canCreate || createFactile.isPending}
        className="w-full"
        size="lg"
      >
        {createFactile.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {t('factileCreate')} ({totalQuestions})
      </Button>
    </div>
  );
}
