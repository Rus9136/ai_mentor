'use client';

import { useState, useRef, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import type { QuizQuestionData } from '@/types/quiz';
import QuizTimer from './QuizTimer';

interface QuizQuestionProps {
  question: QuizQuestionData;
  questionNumber: number;
  totalQuestions: number;
  onAnswer: (selectedOption: number, answerTimeMs: number) => void;
  onTimerTick?: () => void;
  onTimeUp?: () => void;
  hideTimer?: boolean;
}

const OPTION_COLORS = [
  'bg-red-500 hover:bg-red-600 active:bg-red-700',
  'bg-blue-500 hover:bg-blue-600 active:bg-blue-700',
  'bg-amber-500 hover:bg-amber-600 active:bg-amber-700',
  'bg-green-500 hover:bg-green-600 active:bg-green-700',
];

const OPTION_LABELS = ['A', 'B', 'C', 'D'];

export default function QuizQuestion({ question, questionNumber, totalQuestions, onAnswer, onTimerTick, onTimeUp, hideTimer }: QuizQuestionProps) {
  const t = useTranslations('quiz');
  const [selected, setSelected] = useState<number | null>(null);
  const startTime = useRef(Date.now());

  const handleSelect = (index: number) => {
    if (selected !== null) return;
    setSelected(index);
    const answerTimeMs = Date.now() - startTime.current;
    onAnswer(index, answerTimeMs);
  };

  const handleExpire = useCallback(() => {
    onTimeUp?.();
    if (selected === null) {
      // Time expired without answering — send a dummy answer
      onAnswer(-1, question.time_limit_ms);
    }
  }, [selected, onAnswer, onTimeUp, question.time_limit_ms]);

  return (
    <div className="flex min-h-dvh flex-col px-4 py-4">
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <span className="text-sm font-medium text-muted-foreground">
          {t('questionOf', { current: questionNumber, total: totalQuestions })}
        </span>
        {!hideTimer && <QuizTimer totalMs={question.time_limit_ms} onExpire={handleExpire} onUrgentTick={onTimerTick} />}
      </div>

      {/* Question text */}
      <div className="mb-4 flex-1">
        <h2 className="text-lg font-semibold text-foreground leading-relaxed">{question.text}</h2>
      </div>

      {/* Question image */}
      {question.image_url && (
        <div className="mb-4 flex justify-center">
          <img
            src={question.image_url}
            alt=""
            className="max-h-48 rounded-lg object-contain"
          />
        </div>
      )}

      {/* Options grid */}
      <div className="grid grid-cols-1 gap-3 pb-4 sm:grid-cols-2">
        {question.options.map((option, index) => (
          <button
            key={index}
            onClick={() => handleSelect(index)}
            disabled={selected !== null}
            className={`
              flex items-center gap-3 rounded-xl p-4 text-left text-white font-semibold
              transition-all duration-150
              ${selected === index ? 'ring-4 ring-white/50 scale-95' : ''}
              ${selected !== null && selected !== index ? 'opacity-50' : ''}
              ${OPTION_COLORS[index] || OPTION_COLORS[0]}
              disabled:cursor-default
            `}
          >
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white/20 text-sm font-bold">
              {OPTION_LABELS[index]}
            </span>
            <span className="text-sm leading-snug">{option}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
