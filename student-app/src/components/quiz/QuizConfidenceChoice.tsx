'use client';

import { useTranslations } from 'next-intl';
import { Flame, Shield } from 'lucide-react';

interface QuizConfidenceChoiceProps {
  onChoice: (mode: 'risk' | 'safe') => void;
  chosen: 'risk' | 'safe' | null;
}

export default function QuizConfidenceChoice({ onChoice, chosen }: QuizConfidenceChoiceProps) {
  const t = useTranslations('quiz');

  return (
    <div className="mb-4 flex items-center justify-center gap-3">
      <button
        onClick={() => onChoice('risk')}
        disabled={chosen !== null}
        className={`flex flex-col items-center gap-1 rounded-2xl px-5 py-3 font-semibold transition-all ${
          chosen === 'risk'
            ? 'bg-gradient-to-br from-orange-400 to-red-500 text-white scale-105 ring-2 ring-orange-400'
            : chosen === null
              ? 'bg-gradient-to-br from-orange-400 to-red-500 text-white hover:scale-105 active:scale-95'
              : 'bg-muted text-muted-foreground opacity-50'
        }`}
      >
        <Flame className="h-6 w-6" />
        <span className="text-sm">{t('confidence.risk')}</span>
        <span className="text-[10px] opacity-80">{t('confidence.riskDesc')}</span>
      </button>

      <button
        onClick={() => onChoice('safe')}
        disabled={chosen !== null}
        className={`flex flex-col items-center gap-1 rounded-2xl px-5 py-3 font-semibold transition-all ${
          chosen === 'safe'
            ? 'bg-gradient-to-br from-blue-400 to-blue-600 text-white scale-105 ring-2 ring-blue-400'
            : chosen === null
              ? 'bg-gradient-to-br from-blue-400 to-blue-600 text-white hover:scale-105 active:scale-95'
              : 'bg-muted text-muted-foreground opacity-50'
        }`}
      >
        <Shield className="h-6 w-6" />
        <span className="text-sm">{t('confidence.safe')}</span>
        <span className="text-[10px] opacity-80">{t('confidence.safeDesc')}</span>
      </button>
    </div>
  );
}
