'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Check, Loader2 } from 'lucide-react';
import {
  StudentQuestionResponse,
  QuestionType,
  SubmissionResult,
} from '@/lib/api/homework';
import { cn } from '@/lib/utils';

interface ChoiceQuestionProps {
  question: StudentQuestionResponse;
  questionNumber: number;
  onAnswer: (selectedOptions: string[]) => Promise<SubmissionResult>;
  disabled?: boolean;
  feedback?: SubmissionResult | null;
}

export function ChoiceQuestion({
  question,
  questionNumber,
  onAnswer,
  disabled,
  feedback,
}: ChoiceQuestionProps) {
  const t = useTranslations('homework.question');
  const [selectedOptions, setSelectedOptions] = useState<string[]>(
    question.my_selected_options || []
  );
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isMultipleChoice = question.question_type === QuestionType.MULTIPLE_CHOICE;
  const isAnswered = question.is_answered || !!feedback;

  const getOptionLetter = (index: number) => String.fromCharCode(65 + index);

  const handleOptionClick = async (optionId: string) => {
    if (disabled || isAnswered || isSubmitting) return;

    let newSelection: string[];

    if (isMultipleChoice) {
      // Toggle selection for multiple choice
      if (selectedOptions.includes(optionId)) {
        newSelection = selectedOptions.filter((id) => id !== optionId);
      } else {
        newSelection = [...selectedOptions, optionId];
      }
      setSelectedOptions(newSelection);
    } else {
      // Single selection - submit immediately
      newSelection = [optionId];
      setSelectedOptions(newSelection);
      setIsSubmitting(true);
      try {
        await onAnswer(newSelection);
      } finally {
        setIsSubmitting(false);
      }
    }
  };

  const handleSubmitMultiple = async () => {
    if (selectedOptions.length === 0 || isSubmitting) return;
    setIsSubmitting(true);
    try {
      await onAnswer(selectedOptions);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getOptionStyle = (optionId: string) => {
    const isSelected = selectedOptions.includes(optionId);

    if (isAnswered && feedback) {
      // After answer - show correct/incorrect
      const wasSelected = selectedOptions.includes(optionId);
      if (feedback.is_correct && wasSelected) {
        return 'border-green-400 bg-green-50 text-green-800';
      }
      if (!feedback.is_correct && wasSelected) {
        return 'border-red-400 bg-red-50 text-red-800';
      }
      return 'border-gray-200 opacity-50';
    }

    if (isSelected) {
      return 'border-primary bg-primary/5 text-primary';
    }

    return 'border-gray-200 hover:border-primary/50 hover:bg-primary/5';
  };

  return (
    <div className="space-y-4">
      {/* Question Header */}
      <div className="bg-gray-50 rounded-2xl p-4">
        <p className="text-sm text-primary font-medium mb-2">
          {t('number', { current: questionNumber, total: '' }).replace(
            ' из ',
            ''
          )}
        </p>
        <p className="font-semibold text-gray-900">{question.question_text}</p>
      </div>

      {/* Options */}
      <div className="space-y-3">
        {question.options?.map((option, idx) => (
          <button
            key={option.id}
            onClick={() => handleOptionClick(option.id)}
            disabled={disabled || isAnswered || isSubmitting}
            className={cn(
              'w-full p-4 rounded-xl border-2 text-left flex items-center gap-3 transition-all',
              getOptionStyle(option.id),
              (disabled || isAnswered || isSubmitting) && 'cursor-default'
            )}
          >
            <span
              className={cn(
                'w-8 h-8 rounded-full flex items-center justify-center font-semibold shrink-0',
                selectedOptions.includes(option.id)
                  ? 'bg-primary text-white'
                  : 'bg-gray-100 text-gray-600'
              )}
            >
              {isMultipleChoice && selectedOptions.includes(option.id) ? (
                <Check className="w-4 h-4" />
              ) : (
                getOptionLetter(idx)
              )}
            </span>
            <span className="flex-1">{option.text}</span>
          </button>
        ))}
      </div>

      {/* Submit button for multiple choice */}
      {isMultipleChoice && !isAnswered && (
        <button
          onClick={handleSubmitMultiple}
          disabled={selectedOptions.length === 0 || isSubmitting}
          className={cn(
            'w-full py-3 rounded-xl font-medium transition-colors flex items-center justify-center gap-2',
            selectedOptions.length > 0
              ? 'bg-primary text-white hover:bg-primary/90'
              : 'bg-gray-100 text-gray-400 cursor-not-allowed'
          )}
        >
          {isSubmitting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              {t('submitting')}
            </>
          ) : (
            t('submit')
          )}
        </button>
      )}

      {/* Loading indicator for single choice */}
      {!isMultipleChoice && isSubmitting && (
        <div className="flex items-center justify-center py-2">
          <Loader2 className="w-5 h-5 animate-spin text-primary" />
        </div>
      )}
    </div>
  );
}
