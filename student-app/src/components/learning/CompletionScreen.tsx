'use client';

import { useEffect, useRef, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { cn } from '@/lib/utils';
import confetti from 'canvas-confetti';
import {
  CheckCircle2,
  Clock,
  Target,
  ThumbsUp,
  HelpCircle,
  AlertTriangle,
  ArrowRight,
  BookOpen,
  Trophy
} from 'lucide-react';
import { SelfAssessmentRating } from '@/lib/api/textbooks';

interface CompletionScreenProps {
  paragraphTitle: string | null;
  paragraphNumber: number;
  questionsTotal: number;
  questionsCorrect: number;
  timeSpentSeconds: number;
  selfAssessment: SelfAssessmentRating | null;
  nextParagraphId: number | null;
  chapterId: number;
  chapterTitle: string;
  isLastInChapter: boolean;
  onGoToNext: () => void;
  onGoToChapter: () => void;
  className?: string;
}

// Self-assessment config matching SelfAssessment.tsx
const ASSESSMENT_CONFIG: Record<SelfAssessmentRating, {
  icon: React.ElementType;
  color: string;
  bgColor: string;
}> = {
  understood: {
    icon: ThumbsUp,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
  },
  questions: {
    icon: HelpCircle,
    color: 'text-amber-600',
    bgColor: 'bg-amber-50',
  },
  difficult: {
    icon: AlertTriangle,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
  },
};

/**
 * Play a success sound using Web Audio API.
 * This avoids needing an external audio file.
 */
function playSuccessSound() {
  try {
    const audioContext = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();

    // Create a pleasant success chord (C major arpeggio)
    const frequencies = [523.25, 659.25, 783.99]; // C5, E5, G5
    const duration = 0.15;
    const gap = 0.08;

    frequencies.forEach((freq, index) => {
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      oscillator.frequency.value = freq;
      oscillator.type = 'sine';

      const startTime = audioContext.currentTime + index * gap;
      const endTime = startTime + duration;

      gainNode.gain.setValueAtTime(0, startTime);
      gainNode.gain.linearRampToValueAtTime(0.3, startTime + 0.01);
      gainNode.gain.exponentialRampToValueAtTime(0.001, endTime);

      oscillator.start(startTime);
      oscillator.stop(endTime);
    });
  } catch {
    // Silently ignore if Web Audio API is not available
    console.debug('Web Audio API not available for success sound');
  }
}

/**
 * Trigger confetti animation.
 */
function triggerConfetti() {
  // Fire multiple bursts for a better effect
  const count = 200;
  const defaults = {
    origin: { y: 0.7 },
    zIndex: 9999,
  };

  function fire(particleRatio: number, opts: confetti.Options) {
    confetti({
      ...defaults,
      ...opts,
      particleCount: Math.floor(count * particleRatio),
    });
  }

  fire(0.25, {
    spread: 26,
    startVelocity: 55,
  });
  fire(0.2, {
    spread: 60,
  });
  fire(0.35, {
    spread: 100,
    decay: 0.91,
    scalar: 0.8,
  });
  fire(0.1, {
    spread: 120,
    startVelocity: 25,
    decay: 0.92,
    scalar: 1.2,
  });
  fire(0.1, {
    spread: 120,
    startVelocity: 45,
  });
}

/**
 * Format time in seconds to "X мин Y сек" or "Y сек" format.
 */
function formatTime(seconds: number, t: (key: string, params?: Record<string, unknown>) => string): string {
  if (seconds < 60) {
    return t('completion.seconds', { seconds });
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  if (remainingSeconds === 0) {
    return t('completion.minutes', { minutes });
  }
  return `${t('completion.minutes', { minutes })} ${t('completion.seconds', { seconds: remainingSeconds })}`;
}

export function CompletionScreen({
  paragraphTitle,
  paragraphNumber,
  questionsTotal,
  questionsCorrect,
  timeSpentSeconds,
  selfAssessment,
  nextParagraphId,
  chapterId,
  chapterTitle,
  isLastInChapter,
  onGoToNext,
  onGoToChapter,
  className,
}: CompletionScreenProps) {
  const t = useTranslations('paragraph');
  const hasTriggeredRef = useRef(false);

  // Trigger confetti and sound on mount (only once)
  useEffect(() => {
    if (hasTriggeredRef.current) return;
    hasTriggeredRef.current = true;

    // Small delay for better UX
    const timer = setTimeout(() => {
      triggerConfetti();
      playSuccessSound();
    }, 100);

    return () => clearTimeout(timer);
  }, []);

  // Calculate score percentage
  const scorePercentage = questionsTotal > 0
    ? Math.round((questionsCorrect / questionsTotal) * 100)
    : 0;

  // Get assessment config
  const assessmentConfig = selfAssessment ? ASSESSMENT_CONFIG[selfAssessment] : null;
  const AssessmentIcon = assessmentConfig?.icon || CheckCircle2;

  const handleGoToNext = useCallback(() => {
    onGoToNext();
  }, [onGoToNext]);

  const handleGoToChapter = useCallback(() => {
    onGoToChapter();
  }, [onGoToChapter]);

  return (
    <div className={cn('flex flex-col items-center justify-center min-h-[60vh] px-4', className)}>
      {/* Success Icon */}
      <div className="relative mb-6">
        <div className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center animate-bounce-slow">
          <Trophy className="w-12 h-12 text-green-600" />
        </div>
        <div className="absolute -top-1 -right-1 w-8 h-8 bg-amber-400 rounded-full flex items-center justify-center">
          <CheckCircle2 className="w-5 h-5 text-white" />
        </div>
      </div>

      {/* Title */}
      <h2 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2 text-center">
        {t('completion.title')}
      </h2>

      <p className="text-gray-600 text-center mb-8">
        {paragraphTitle ? `§${paragraphNumber}. ${paragraphTitle}` : `§${paragraphNumber}`}
      </p>

      {/* Stats Cards */}
      <div className="grid grid-cols-3 gap-3 md:gap-4 w-full max-w-md mb-8">
        {/* Score */}
        <div className="bg-white rounded-xl shadow-md p-4 text-center">
          <div className={cn(
            'w-12 h-12 mx-auto rounded-full flex items-center justify-center mb-2',
            scorePercentage >= 80 ? 'bg-green-100' : scorePercentage >= 60 ? 'bg-amber-100' : 'bg-red-100'
          )}>
            <Target className={cn(
              'w-6 h-6',
              scorePercentage >= 80 ? 'text-green-600' : scorePercentage >= 60 ? 'text-amber-600' : 'text-red-600'
            )} />
          </div>
          <div className="font-bold text-lg text-gray-900">
            {questionsTotal > 0 ? `${questionsCorrect}/${questionsTotal}` : '-'}
          </div>
          <div className="text-xs text-gray-500">
            {t('completion.questionsLabel')}
          </div>
        </div>

        {/* Time */}
        <div className="bg-white rounded-xl shadow-md p-4 text-center">
          <div className="w-12 h-12 mx-auto rounded-full bg-blue-100 flex items-center justify-center mb-2">
            <Clock className="w-6 h-6 text-blue-600" />
          </div>
          <div className="font-bold text-lg text-gray-900">
            {Math.floor(timeSpentSeconds / 60) || '<1'}
          </div>
          <div className="text-xs text-gray-500">
            {t('completion.timeLabel')}
          </div>
        </div>

        {/* Self Assessment */}
        <div className="bg-white rounded-xl shadow-md p-4 text-center">
          <div className={cn(
            'w-12 h-12 mx-auto rounded-full flex items-center justify-center mb-2',
            assessmentConfig?.bgColor || 'bg-gray-100'
          )}>
            <AssessmentIcon className={cn(
              'w-6 h-6',
              assessmentConfig?.color || 'text-gray-400'
            )} />
          </div>
          <div className="font-bold text-lg text-gray-900 truncate">
            {selfAssessment ? t(`completion.selfAssessment.${selfAssessment}`) : '-'}
          </div>
          <div className="text-xs text-gray-500">
            {t('completion.assessmentLabel')}
          </div>
        </div>
      </div>

      {/* Chapter Complete Message */}
      {isLastInChapter && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 mb-6 text-center">
          <p className="text-amber-800 font-medium">
            {t('completion.chapterComplete')}
          </p>
          <p className="text-amber-600 text-sm mt-1">
            {chapterTitle}
          </p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-3 w-full max-w-md">
        {/* To Chapter */}
        <button
          onClick={handleGoToChapter}
          className={cn(
            'flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-medium transition-all duration-200',
            'border-2 border-gray-200 text-gray-700 hover:bg-gray-50 hover:border-gray-300 active:scale-95',
            nextParagraphId ? 'flex-1' : 'flex-1'
          )}
        >
          <BookOpen className="w-5 h-5" />
          {t('completion.toChapter')}
        </button>

        {/* Next Paragraph */}
        {nextParagraphId && !isLastInChapter && (
          <button
            onClick={handleGoToNext}
            className={cn(
              'flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-medium transition-all duration-200',
              'bg-amber-500 text-white hover:bg-amber-600 active:scale-95 flex-1'
            )}
          >
            {t('completion.nextParagraph')}
            <ArrowRight className="w-5 h-5" />
          </button>
        )}
      </div>
    </div>
  );
}
