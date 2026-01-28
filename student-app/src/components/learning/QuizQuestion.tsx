'use client';

import { cn } from '@/lib/utils';
import { TestQuestion, QuestionOption } from '@/lib/api/tests';
import { CheckCircle2, XCircle } from 'lucide-react';
import { MathText } from '@/components/common/MathText';

interface QuizQuestionProps {
  question: TestQuestion;
  questionNumber: number;
  totalQuestions: number;
  selectedAnswer: number[] | null;
  onAnswer: (optionIds: number[]) => void;
  showResult?: boolean;
  isCorrect?: boolean;
  correctOptionIds?: number[];
  className?: string;
}

export function QuizQuestion({
  question,
  questionNumber,
  totalQuestions,
  selectedAnswer,
  onAnswer,
  showResult = false,
  isCorrect,
  correctOptionIds = [],
  className,
}: QuizQuestionProps) {
  const isMultipleChoice = question.question_type === 'multiple_choice';
  const isTrueFalse = question.question_type === 'true_false';

  const handleOptionClick = (optionId: number) => {
    if (showResult) return;

    if (isMultipleChoice) {
      const currentSelection = selectedAnswer || [];
      const newSelection = currentSelection.includes(optionId)
        ? currentSelection.filter(id => id !== optionId)
        : [...currentSelection, optionId];
      onAnswer(newSelection);
    } else {
      onAnswer([optionId]);
    }
  };

  // For true/false, create virtual options if not provided
  const displayOptions: (QuestionOption | { id: number; option_text: string })[] =
    isTrueFalse && (!question.options || question.options.length === 0)
      ? [
          { id: -1, option_text: 'True' },
          { id: -2, option_text: 'False' },
        ]
      : question.options;

  const getOptionStyle = (optionId: number) => {
    const isSelected = selectedAnswer?.includes(optionId);

    if (!showResult) {
      return cn(
        'border-2 transition-all duration-200 cursor-pointer',
        isSelected
          ? 'border-amber-500 bg-amber-50'
          : 'border-gray-200 hover:border-amber-300 hover:bg-amber-50/50'
      );
    }

    // After showing result
    const isCorrectOption = correctOptionIds.includes(optionId);

    if (isCorrectOption) {
      return 'border-2 border-green-500 bg-green-50';
    }
    if (isSelected && !isCorrectOption) {
      return 'border-2 border-red-500 bg-red-50';
    }
    return 'border-2 border-gray-200 opacity-60';
  };

  // Generate option letter (A, B, C, D...)
  const getOptionLetter = (index: number) => String.fromCharCode(65 + index);

  return (
    <div className={cn('bg-white rounded-2xl p-6', className)}>
      {/* Question header */}
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-medium text-amber-600 bg-amber-100 px-3 py-1 rounded-full">
          {questionNumber} / {totalQuestions}
        </span>
        <span className="text-sm text-gray-500">
          {question.points} {question.points === 1 ? 'point' : 'points'}
        </span>
      </div>

      {/* Question text */}
      <h3 className="text-lg font-semibold text-gray-900 mb-6">
        <MathText>{question.question_text}</MathText>
      </h3>

      {/* Options */}
      <div className="space-y-3">
        {displayOptions.map((option, index) => {
          const isSelected = selectedAnswer?.includes(option.id);
          const isCorrectOption = showResult && correctOptionIds.includes(option.id);
          const isWrongSelection = showResult && isSelected && !isCorrectOption;

          return (
            <button
              key={option.id}
              onClick={() => handleOptionClick(option.id)}
              disabled={showResult}
              className={cn(
                'w-full p-4 rounded-xl text-left flex items-center gap-3',
                getOptionStyle(option.id),
                showResult && 'cursor-default'
              )}
            >
              {/* Option indicator */}
              <div className={cn(
                'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 font-semibold text-sm',
                !showResult && isSelected && 'bg-amber-500 text-white',
                !showResult && !isSelected && 'bg-gray-100 text-gray-600',
                showResult && isCorrectOption && 'bg-green-500 text-white',
                showResult && isWrongSelection && 'bg-red-500 text-white',
                showResult && !isCorrectOption && !isSelected && 'bg-gray-100 text-gray-400'
              )}>
                {showResult && isCorrectOption ? (
                  <CheckCircle2 className="w-5 h-5" />
                ) : showResult && isWrongSelection ? (
                  <XCircle className="w-5 h-5" />
                ) : (
                  getOptionLetter(index)
                )}
              </div>

              {/* Option text */}
              <span className={cn(
                'flex-1',
                showResult && !isCorrectOption && !isSelected && 'text-gray-400'
              )}>
                <MathText>{option.option_text}</MathText>
              </span>

              {/* Multiple choice checkbox indicator */}
              {isMultipleChoice && !showResult && (
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

      {/* Result indicator */}
      {showResult && (
        <div className={cn(
          'mt-6 p-4 rounded-xl flex items-center gap-2',
          isCorrect ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
        )}>
          {isCorrect ? (
            <>
              <CheckCircle2 className="w-5 h-5 text-green-600" />
              <span className="font-semibold text-green-700">Correct!</span>
            </>
          ) : (
            <>
              <XCircle className="w-5 h-5 text-red-600" />
              <span className="font-semibold text-red-700">Incorrect</span>
            </>
          )}
        </div>
      )}
    </div>
  );
}
