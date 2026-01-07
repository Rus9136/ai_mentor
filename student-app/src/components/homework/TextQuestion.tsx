'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Loader2, Send } from 'lucide-react';
import {
  StudentQuestionResponse,
  QuestionType,
  SubmissionResult,
} from '@/lib/api/homework';
import { cn } from '@/lib/utils';

interface TextQuestionProps {
  question: StudentQuestionResponse;
  questionNumber: number;
  onAnswer: (answerText: string) => Promise<SubmissionResult>;
  disabled?: boolean;
  feedback?: SubmissionResult | null;
}

export function TextQuestion({
  question,
  questionNumber,
  onAnswer,
  disabled,
  feedback,
}: TextQuestionProps) {
  const t = useTranslations('homework.question');
  const [answer, setAnswer] = useState(question.my_answer || '');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isOpenEnded = question.question_type === QuestionType.OPEN_ENDED;
  const isAnswered = question.is_answered || !!feedback;

  const handleSubmit = async () => {
    if (!answer.trim() || isSubmitting) return;
    setIsSubmitting(true);
    try {
      await onAnswer(answer.trim());
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Submit on Enter for short answer (not open-ended)
    if (!isOpenEnded && e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
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

      {/* Answer Input */}
      <div className="space-y-3">
        {isOpenEnded ? (
          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled || isAnswered || isSubmitting}
            placeholder={t('textPlaceholder')}
            rows={6}
            className={cn(
              'w-full p-4 rounded-xl border-2 resize-none transition-colors focus:outline-none focus:ring-2 focus:ring-primary/20',
              isAnswered
                ? feedback?.is_correct
                  ? 'border-green-300 bg-green-50'
                  : feedback?.is_correct === false
                  ? 'border-red-300 bg-red-50'
                  : 'border-amber-300 bg-amber-50'
                : 'border-gray-200 focus:border-primary'
            )}
          />
        ) : (
          <input
            type="text"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled || isAnswered || isSubmitting}
            placeholder={t('textPlaceholder')}
            className={cn(
              'w-full p-4 rounded-xl border-2 transition-colors focus:outline-none focus:ring-2 focus:ring-primary/20',
              isAnswered
                ? feedback?.is_correct
                  ? 'border-green-300 bg-green-50'
                  : 'border-red-300 bg-red-50'
                : 'border-gray-200 focus:border-primary'
            )}
          />
        )}

        {/* Submit Button */}
        {!isAnswered && (
          <button
            onClick={handleSubmit}
            disabled={!answer.trim() || isSubmitting}
            className={cn(
              'w-full py-3 rounded-xl font-medium transition-colors flex items-center justify-center gap-2',
              answer.trim()
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
              <>
                <Send className="w-4 h-4" />
                {t('submit')}
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
}
