'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { cn } from '@/lib/utils';
import { EmbeddedQuestion as EmbeddedQuestionType, AnswerResult } from '@/lib/api/textbooks';
import { CheckCircle2, XCircle, HelpCircle, Lightbulb, ChevronRight } from 'lucide-react';

interface EmbeddedQuestionProps {
  question: EmbeddedQuestionType;
  questionNumber: number;
  totalQuestions: number;
  onAnswer: (questionId: number, answer: string | string[]) => Promise<AnswerResult>;
  onNext?: () => void;
  isLast?: boolean;
  className?: string;
}

type AnswerState = 'unanswered' | 'correct' | 'incorrect';

export function EmbeddedQuestion({
  question,
  questionNumber,
  totalQuestions,
  onAnswer,
  onNext,
  isLast = false,
  className,
}: EmbeddedQuestionProps) {
  const t = useTranslations('paragraph');
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [selectedMultiple, setSelectedMultiple] = useState<string[]>([]);
  const [answerState, setAnswerState] = useState<AnswerState>('unanswered');
  const [result, setResult] = useState<AnswerResult | null>(null);
  const [showHint, setShowHint] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isMultipleChoice = question.question_type === 'multiple_choice';
  const isTrueFalse = question.question_type === 'true_false';
  const hasAnswered = answerState !== 'unanswered';

  const handleOptionClick = (optionId: string) => {
    if (hasAnswered) return;

    if (isMultipleChoice) {
      setSelectedMultiple(prev =>
        prev.includes(optionId)
          ? prev.filter(id => id !== optionId)
          : [...prev, optionId]
      );
    } else {
      setSelectedAnswer(optionId);
    }
  };

  const handleSubmit = async () => {
    if (isSubmitting) return;

    const answer = isMultipleChoice ? selectedMultiple : selectedAnswer;
    if (!answer || (Array.isArray(answer) && answer.length === 0)) return;

    setIsSubmitting(true);
    try {
      const answerResult = await onAnswer(question.id, answer);
      setResult(answerResult);
      setAnswerState(answerResult.is_correct ? 'correct' : 'incorrect');
    } catch (error) {
      console.error('Failed to submit answer:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getOptionStyle = (optionId: string) => {
    const isSelected = isMultipleChoice
      ? selectedMultiple.includes(optionId)
      : selectedAnswer === optionId;

    if (!hasAnswered) {
      return cn(
        'border-2 transition-all duration-200 cursor-pointer',
        isSelected
          ? 'border-amber-500 bg-amber-50'
          : 'border-gray-200 hover:border-amber-300 hover:bg-amber-50/50'
      );
    }

    // After answering - show correct/incorrect
    const isCorrectOption = result?.correct_answer === optionId ||
      (Array.isArray(result?.correct_answer) && result.correct_answer.includes(optionId));

    if (isCorrectOption) {
      return 'border-2 border-green-500 bg-green-50';
    }
    if (isSelected && !isCorrectOption) {
      return 'border-2 border-red-500 bg-red-50';
    }
    return 'border-2 border-gray-200 opacity-60';
  };

  const trueFalseOptions = isTrueFalse ? [
    { id: 'true', text: t('question.true') },
    { id: 'false', text: t('question.false') },
  ] : null;

  const displayOptions = trueFalseOptions || question.options || [];

  return (
    <div className={cn('bg-white rounded-2xl shadow-md p-6', className)}>
      {/* Question header */}
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-medium text-amber-600 bg-amber-100 px-3 py-1 rounded-full">
          {t('question.number', { current: questionNumber, total: totalQuestions })}
        </span>
        {question.hint && !hasAnswered && (
          <button
            onClick={() => setShowHint(!showHint)}
            className="flex items-center gap-1 text-sm text-gray-500 hover:text-amber-600 transition-colors"
          >
            <Lightbulb className="w-4 h-4" />
            {t('question.hint')}
          </button>
        )}
      </div>

      {/* Hint */}
      {showHint && question.hint && !hasAnswered && (
        <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <p className="text-sm text-amber-800">{question.hint}</p>
        </div>
      )}

      {/* Question text */}
      <h3 className="text-lg font-semibold text-gray-900 mb-6">
        {question.question_text}
      </h3>

      {/* Options */}
      <div className="space-y-3">
        {displayOptions.map((option) => {
          const isSelected = isMultipleChoice
            ? selectedMultiple.includes(option.id)
            : selectedAnswer === option.id;
          const isCorrectOption = hasAnswered && (
            result?.correct_answer === option.id ||
            (Array.isArray(result?.correct_answer) && result.correct_answer.includes(option.id))
          );
          const isWrongSelection = hasAnswered && isSelected && !isCorrectOption;

          return (
            <button
              key={option.id}
              onClick={() => handleOptionClick(option.id)}
              disabled={hasAnswered}
              className={cn(
                'w-full p-4 rounded-xl text-left flex items-center gap-3',
                getOptionStyle(option.id),
                hasAnswered && 'cursor-default'
              )}
            >
              {/* Option indicator */}
              <div className={cn(
                'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 font-semibold',
                !hasAnswered && isSelected && 'bg-amber-500 text-white',
                !hasAnswered && !isSelected && 'bg-gray-100 text-gray-600',
                hasAnswered && isCorrectOption && 'bg-green-500 text-white',
                hasAnswered && isWrongSelection && 'bg-red-500 text-white',
                hasAnswered && !isCorrectOption && !isSelected && 'bg-gray-100 text-gray-400'
              )}>
                {hasAnswered && isCorrectOption ? (
                  <CheckCircle2 className="w-5 h-5" />
                ) : hasAnswered && isWrongSelection ? (
                  <XCircle className="w-5 h-5" />
                ) : (
                  option.id.toUpperCase()
                )}
              </div>

              {/* Option text */}
              <span className={cn(
                'flex-1',
                hasAnswered && !isCorrectOption && !isSelected && 'text-gray-400'
              )}>
                {option.text}
              </span>

              {/* Multiple choice checkbox indicator */}
              {isMultipleChoice && !hasAnswered && (
                <div className={cn(
                  'w-5 h-5 rounded border-2 flex items-center justify-center',
                  isSelected ? 'border-amber-500 bg-amber-500' : 'border-gray-300'
                )}>
                  {isSelected && <CheckCircle2 className="w-3 h-3 text-white" />}
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Result feedback */}
      {hasAnswered && result && (
        <div className={cn(
          'mt-6 p-4 rounded-xl',
          answerState === 'correct' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
        )}>
          <div className="flex items-center gap-2 mb-2">
            {answerState === 'correct' ? (
              <CheckCircle2 className="w-5 h-5 text-green-600" />
            ) : (
              <XCircle className="w-5 h-5 text-red-600" />
            )}
            <span className={cn(
              'font-semibold',
              answerState === 'correct' ? 'text-green-700' : 'text-red-700'
            )}>
              {answerState === 'correct' ? t('question.correct') : t('question.incorrect')}
            </span>
          </div>
          {result.explanation && (
            <p className="text-sm text-gray-700">{result.explanation}</p>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="mt-6 flex justify-end gap-3">
        {!hasAnswered ? (
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || (!selectedAnswer && selectedMultiple.length === 0)}
            className={cn(
              'px-6 py-2.5 rounded-xl font-medium transition-all duration-200',
              (selectedAnswer || selectedMultiple.length > 0)
                ? 'bg-amber-500 text-white hover:bg-amber-600 active:scale-95'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            )}
          >
            {isSubmitting ? t('question.checking') : t('question.submit')}
          </button>
        ) : (
          <button
            onClick={onNext}
            className="px-6 py-2.5 rounded-xl font-medium bg-amber-500 text-white hover:bg-amber-600 active:scale-95 transition-all duration-200 flex items-center gap-2"
          >
            {isLast ? t('question.finish') : t('question.next')}
            <ChevronRight className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}
