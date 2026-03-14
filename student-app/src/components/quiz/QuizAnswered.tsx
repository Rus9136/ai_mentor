'use client';

import { useTranslations } from 'next-intl';
import { CheckCircle2, Loader2 } from 'lucide-react';

interface QuizAnsweredProps {
  score: number | null;
  isCorrect: boolean | null;
}

export default function QuizAnswered({ score, isCorrect }: QuizAnsweredProps) {
  const t = useTranslations('quiz');

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center px-4 text-center">
      {isCorrect !== null ? (
        <>
          <CheckCircle2
            className={`mb-4 h-16 w-16 ${isCorrect ? 'text-green-500' : 'text-red-400'}`}
          />
          <h2 className="mb-2 text-xl font-bold text-foreground">{t('answerSubmitted')}</h2>
          {score !== null && score > 0 && (
            <p className="text-2xl font-bold text-primary">{t('points', { score })}</p>
          )}
        </>
      ) : (
        <>
          <Loader2 className="mb-4 h-12 w-12 animate-spin text-primary" />
          <h2 className="text-xl font-bold text-foreground">{t('answerSubmitted')}</h2>
        </>
      )}
      <p className="mt-4 text-sm text-muted-foreground">{t('waiting')}</p>
    </div>
  );
}
