'use client';

import { useState, useRef } from 'react';
import { useTranslations } from 'next-intl';
import type { QuizQuestionData } from '@/types/quiz';
import QuizTimer from './QuizTimer';

interface QuizShortAnswerProps {
  question: QuizQuestionData;
  questionNumber: number;
  totalQuestions: number;
  onAnswer: (textAnswer: string, answerTimeMs: number) => void;
  onTimerTick?: () => void;
  onTimeUp?: () => void;
  hideTimer?: boolean;
}

export default function QuizShortAnswer({
  question,
  questionNumber,
  totalQuestions,
  onAnswer,
  onTimerTick,
  onTimeUp,
  hideTimer,
}: QuizShortAnswerProps) {
  const t = useTranslations('quiz');
  const [text, setText] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const startTime = useRef(Date.now());

  const handleSubmit = () => {
    if (submitted || !text.trim()) return;
    setSubmitted(true);
    const answerTimeMs = Date.now() - startTime.current;
    onAnswer(text.trim(), answerTimeMs);
  };

  const handleTimeUp = () => {
    if (!submitted) {
      setSubmitted(true);
      const answerTimeMs = Date.now() - startTime.current;
      onAnswer(text.trim() || '', answerTimeMs);
    }
    onTimeUp?.();
  };

  return (
    <div className="flex min-h-[70vh] flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3">
        <span className="text-sm font-medium text-white/80">
          {questionNumber}/{totalQuestions}
        </span>
        {!hideTimer && question.time_limit_ms > 0 && (
          <QuizTimer
            totalMs={question.time_limit_ms}
            onUrgentTick={onTimerTick}
            onExpire={handleTimeUp}
          />
        )}
      </div>

      {/* Question */}
      <div className="flex-1 px-4 pb-4">
        <div className="mb-6 rounded-xl bg-white/10 p-4">
          <p className="text-center text-lg font-bold text-white">{question.text}</p>
          {question.image_url && (
            <img src={question.image_url} alt="" className="mx-auto mt-3 max-h-48 rounded-lg" />
          )}
        </div>

        {/* Text input */}
        <div className="space-y-4">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={submitted}
            placeholder={t('typeAnswer')}
            className="w-full rounded-xl border-2 border-white/20 bg-white/10 p-4 text-lg text-white placeholder-white/40 focus:border-white/50 focus:outline-none disabled:opacity-50"
            rows={3}
            autoFocus
          />
          <button
            onClick={handleSubmit}
            disabled={submitted || !text.trim()}
            className="w-full rounded-xl bg-white py-4 text-lg font-bold text-gray-900 transition-colors hover:bg-white/90 disabled:opacity-50"
          >
            {submitted ? t('answerSent') : t('submit')}
          </button>
        </div>
      </div>
    </div>
  );
}
