'use client';

import { useState, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { ChevronDown, ChevronRight, Plus, X, Loader2 } from 'lucide-react';
import { Checkbox } from '@/components/ui/checkbox';
import { Button } from '@/components/ui/button';
import { useChapterQuestions } from '@/lib/hooks/use-quiz';
import type { ParagraphQuestions, CustomQuestion } from '@/lib/api/quiz';

interface QuestionPickerProps {
  chapterId?: number;
  selectedQuestionIds: number[];
  onSelectedChange: (ids: number[]) => void;
  customQuestions: CustomQuestion[];
  onCustomQuestionsChange: (questions: CustomQuestion[]) => void;
}

export default function QuestionPicker({
  chapterId,
  selectedQuestionIds,
  onSelectedChange,
  customQuestions,
  onCustomQuestionsChange,
}: QuestionPickerProps) {
  const t = useTranslations('quiz');
  const { data: paragraphs, isLoading } = useChapterQuestions(chapterId);
  const [expanded, setExpanded] = useState<Record<number | string, boolean>>({});
  const [showAddForm, setShowAddForm] = useState(false);

  const toggleExpand = useCallback((key: number | string) => {
    setExpanded((prev) => ({ ...prev, [key]: !prev[key] }));
  }, []);

  const toggleQuestion = useCallback(
    (questionId: number) => {
      onSelectedChange(
        selectedQuestionIds.includes(questionId)
          ? selectedQuestionIds.filter((id) => id !== questionId)
          : [...selectedQuestionIds, questionId]
      );
    },
    [selectedQuestionIds, onSelectedChange]
  );

  const toggleParagraph = useCallback(
    (para: ParagraphQuestions) => {
      const paraQIds = para.questions.map((q) => q.id);
      const allSelected = paraQIds.every((id) => selectedQuestionIds.includes(id));
      if (allSelected) {
        onSelectedChange(selectedQuestionIds.filter((id) => !paraQIds.includes(id)));
      } else {
        const newIds = new Set([...selectedQuestionIds, ...paraQIds]);
        onSelectedChange(Array.from(newIds));
      }
    },
    [selectedQuestionIds, onSelectedChange]
  );

  const toggleAll = useCallback(() => {
    if (!paragraphs) return;
    const allQIds = paragraphs.flatMap((p) => p.questions.map((q) => q.id));
    const allSelected = allQIds.every((id) => selectedQuestionIds.includes(id));
    onSelectedChange(allSelected ? [] : allQIds);
  }, [paragraphs, selectedQuestionIds, onSelectedChange]);

  const removeCustomQuestion = useCallback(
    (index: number) => {
      onCustomQuestionsChange(customQuestions.filter((_, i) => i !== index));
    },
    [customQuestions, onCustomQuestionsChange]
  );

  const totalSelected = selectedQuestionIds.length + customQuestions.length;
  const allBankIds = paragraphs?.flatMap((p) => p.questions.map((q) => q.id)) ?? [];
  const allBankSelected = allBankIds.length > 0 && allBankIds.every((id) => selectedQuestionIds.includes(id));

  if (chapterId && isLoading) {
    return (
      <div className="flex items-center justify-center py-8 text-muted-foreground">
        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        {t('loading')}
      </div>
    );
  }

  return (
    <div className="space-y-1">
      <div className="mb-3 flex items-center justify-between">
        <label className="text-sm font-medium">{t('pickQuestions')}</label>
        <span className="text-sm text-muted-foreground">
          {t('selectedCount', { count: totalSelected })}
        </span>
      </div>

      {/* Select all bank questions */}
      {paragraphs && paragraphs.length > 0 && (
        <button
          type="button"
          onClick={toggleAll}
          className="mb-2 flex w-full items-center gap-2 rounded-lg border bg-muted/30 px-3 py-2 text-left text-sm hover:bg-muted/50"
        >
          <Checkbox checked={allBankSelected} />
          <span>{t('selectAll')}</span>
        </button>
      )}

      {/* Paragraph accordion */}
      {paragraphs?.map((para) => {
        const isOpen = expanded[para.paragraph_id];
        const paraQIds = para.questions.map((q) => q.id);
        const selectedInPara = paraQIds.filter((id) => selectedQuestionIds.includes(id)).length;
        const allInParaSelected = paraQIds.length > 0 && selectedInPara === paraQIds.length;

        return (
          <div key={para.paragraph_id} className="rounded-lg border">
            {/* Paragraph header */}
            <button
              type="button"
              onClick={() => toggleExpand(para.paragraph_id)}
              className="flex w-full items-center gap-2 px-3 py-2.5 text-left text-sm hover:bg-muted/50"
            >
              {isOpen ? (
                <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
              ) : (
                <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
              )}
              <Checkbox
                checked={allInParaSelected}
                onClick={(e) => {
                  e.stopPropagation();
                  toggleParagraph(para);
                }}
              />
              <span className="flex-1 font-medium">
                §{para.paragraph_number}. {para.paragraph_title}
              </span>
              <span className="shrink-0 rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                {selectedInPara}/{paraQIds.length}
              </span>
            </button>

            {/* Expanded questions */}
            {isOpen && (
              <div className="border-t px-3 py-2 space-y-1.5">
                {para.questions.map((q, qi) => {
                  const isSelected = selectedQuestionIds.includes(q.id);
                  return (
                    <div key={q.id}>
                      <button
                        type="button"
                        onClick={() => toggleQuestion(q.id)}
                        className={`flex w-full items-start gap-2 rounded-md px-2 py-1.5 text-left text-sm transition-colors ${
                          isSelected ? 'bg-primary/5' : 'hover:bg-muted/50'
                        }`}
                      >
                        <Checkbox checked={isSelected} className="mt-0.5" />
                        <span className="flex-1">
                          <span className="text-muted-foreground">{qi + 1}.</span>{' '}
                          {q.question_text.length > 120
                            ? q.question_text.slice(0, 120) + '...'
                            : q.question_text}
                        </span>
                      </button>
                      {/* Options preview (only when selected) */}
                      {isSelected && q.options.length > 0 && (
                        <div className="ml-8 mt-1 mb-1 flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-muted-foreground">
                          {q.options.map((o, oi) => (
                            <span key={oi} className={o.is_correct ? 'font-semibold text-green-600' : ''}>
                              {String.fromCharCode(65 + oi)}) {o.text.length > 40 ? o.text.slice(0, 40) + '...' : o.text}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}

      {/* No bank questions */}
      {(!paragraphs || paragraphs.length === 0) && !isLoading && (
        <p className="py-4 text-center text-sm text-muted-foreground">{t('noBankQuestions')}</p>
      )}

      {/* Custom questions section */}
      {customQuestions.length > 0 && (
        <div className="rounded-lg border">
          <button
            type="button"
            onClick={() => toggleExpand('custom')}
            className="flex w-full items-center gap-2 px-3 py-2.5 text-left text-sm hover:bg-muted/50"
          >
            {expanded['custom'] ? (
              <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
            )}
            <span className="flex-1 font-medium">{t('myQuestions')}</span>
            <span className="shrink-0 rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
              {customQuestions.length}
            </span>
          </button>
          {expanded['custom'] && (
            <div className="border-t px-3 py-2 space-y-1.5">
              {customQuestions.map((cq, i) => (
                <div key={i} className="flex items-start gap-2 rounded-md bg-primary/5 px-2 py-1.5 text-sm">
                  <span className="flex-1">
                    <span className="text-muted-foreground">{i + 1}.</span>{' '}
                    {cq.question_text.length > 120 ? cq.question_text.slice(0, 120) + '...' : cq.question_text}
                    <span className="ml-2 text-xs text-muted-foreground">
                      ({cq.options.length} {t('optionsCount')})
                    </span>
                  </span>
                  <button
                    type="button"
                    onClick={() => removeCustomQuestion(i)}
                    className="shrink-0 rounded p-0.5 text-muted-foreground hover:text-destructive"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Add custom question button / form */}
      {showAddForm ? (
        <AddCustomQuestionForm
          onAdd={(q) => {
            onCustomQuestionsChange([...customQuestions, q]);
            setShowAddForm(false);
          }}
          onCancel={() => setShowAddForm(false)}
        />
      ) : (
        <button
          type="button"
          onClick={() => setShowAddForm(true)}
          className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-dashed py-2.5 text-sm text-muted-foreground hover:border-primary hover:text-primary"
        >
          <Plus className="h-4 w-4" />
          {t('addCustomQuestion')}
        </button>
      )}

      {/* Total counter */}
      {totalSelected > 0 && (
        <div className="rounded-lg bg-primary/10 px-3 py-2 text-center text-sm font-medium text-primary">
          {t('selectedCount', { count: totalSelected })}
        </div>
      )}
    </div>
  );
}

// ── Inline form for adding a custom question ──

function AddCustomQuestionForm({
  onAdd,
  onCancel,
}: {
  onAdd: (q: CustomQuestion) => void;
  onCancel: () => void;
}) {
  const t = useTranslations('quiz');
  const [questionText, setQuestionText] = useState('');
  const [options, setOptions] = useState(['', '', '', '']);
  const [correctOption, setCorrectOption] = useState(0);

  const handleAddOption = () => {
    if (options.length < 6) setOptions([...options, '']);
  };

  const handleRemoveOption = (index: number) => {
    if (options.length <= 2) return;
    const newOptions = options.filter((_, i) => i !== index);
    setOptions(newOptions);
    if (correctOption >= newOptions.length) setCorrectOption(0);
    else if (correctOption > index) setCorrectOption(correctOption - 1);
  };

  const handleSubmit = () => {
    const trimmed = questionText.trim();
    const trimmedOptions = options.map((o) => o.trim()).filter((o) => o);
    if (!trimmed || trimmedOptions.length < 2) return;
    onAdd({
      question_text: trimmed,
      options: trimmedOptions,
      correct_option: Math.min(correctOption, trimmedOptions.length - 1),
    });
  };

  const canSubmit = questionText.trim().length > 0 && options.filter((o) => o.trim()).length >= 2;

  return (
    <div className="rounded-lg border bg-card p-4 space-y-3">
      <label className="block text-sm font-medium">{t('questionText')}</label>
      <textarea
        className="w-full rounded-lg border bg-background px-3 py-2 text-sm"
        rows={2}
        placeholder={t('typeQuestion')}
        value={questionText}
        onChange={(e) => setQuestionText(e.target.value)}
      />

      <label className="block text-sm font-medium">{t('options')}</label>
      <div className="space-y-2">
        {options.map((opt, i) => (
          <div key={i} className="flex items-center gap-2">
            <input
              type="radio"
              name="correct"
              checked={correctOption === i}
              onChange={() => setCorrectOption(i)}
              className="h-4 w-4 text-primary"
            />
            <span className="text-sm font-medium text-muted-foreground w-5">
              {String.fromCharCode(65 + i)})
            </span>
            <input
              type="text"
              className="flex-1 rounded-lg border bg-background px-3 py-1.5 text-sm"
              placeholder={`${t('option')} ${String.fromCharCode(65 + i)}`}
              value={opt}
              onChange={(e) => {
                const newOpts = [...options];
                newOpts[i] = e.target.value;
                setOptions(newOpts);
              }}
            />
            {options.length > 2 && (
              <button
                type="button"
                onClick={() => handleRemoveOption(i)}
                className="rounded p-1 text-muted-foreground hover:text-destructive"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        ))}
      </div>

      {options.length < 6 && (
        <button
          type="button"
          onClick={handleAddOption}
          className="flex items-center gap-1 text-xs text-muted-foreground hover:text-primary"
        >
          <Plus className="h-3 w-3" /> {t('addOption')}
        </button>
      )}

      <p className="text-xs text-muted-foreground">{t('correctOptionHint')}</p>

      <div className="flex justify-end gap-2">
        <Button type="button" variant="outline" size="sm" onClick={onCancel}>
          {t('cancel')}
        </Button>
        <Button type="button" size="sm" onClick={handleSubmit} disabled={!canSubmit}>
          {t('saveQuestion')}
        </Button>
      </div>
    </div>
  );
}
