'use client';

import { useState } from 'react';
import { ChevronLeft, ChevronRight, Layers } from 'lucide-react';
import type { FlashCard } from '@/lib/api/textbooks';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type TranslateFunction = (key: string, values?: Record<string, any>) => string;

interface FlashCardsProps {
  cards: FlashCard[];
  t: TranslateFunction;
}

export function FlashCards({ cards, t }: FlashCardsProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);

  if (!cards || cards.length === 0) {
    return (
      <div className="card-elevated p-8 text-center">
        <Layers className="mx-auto h-12 w-12 text-muted-foreground/50" />
        <p className="mt-4 text-muted-foreground">{t('noCards')}</p>
      </div>
    );
  }

  const currentCard = cards[currentIndex];

  const goNext = () => {
    if (currentIndex < cards.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setIsFlipped(false);
    }
  };

  const goPrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
      setIsFlipped(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>{t('cardProgress', { current: currentIndex + 1, total: cards.length })}</span>
        <span>{t('tapToFlip')}</span>
      </div>

      <div
        onClick={() => setIsFlipped(!isFlipped)}
        className="card-elevated cursor-pointer min-h-[250px] flex items-center justify-center p-8 transition-all hover:shadow-soft-lg"
        style={{ perspective: '1000px' }}
      >
        <div
          className={`w-full text-center transition-transform duration-500 ${
            isFlipped ? 'scale-y-[-1]' : ''
          }`}
          style={{ transformStyle: 'preserve-3d' }}
        >
          <div className={isFlipped ? 'scale-y-[-1]' : ''}>
            {!isFlipped ? (
              <div>
                <p className="text-xs text-muted-foreground mb-2">{t('cardFront')}</p>
                <p className="text-xl font-semibold text-foreground">{currentCard.front}</p>
              </div>
            ) : (
              <div>
                <p className="text-xs text-muted-foreground mb-2">{t('cardBack')}</p>
                <p className="text-lg text-foreground">{currentCard.back}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <button
          onClick={goPrev}
          disabled={currentIndex === 0}
          className="flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium bg-muted text-muted-foreground hover:bg-muted/80 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          <ChevronLeft className="h-4 w-4" />
          {t('previousCard')}
        </button>

        <div className="flex gap-1">
          {cards.map((_, i) => (
            <button
              key={i}
              onClick={() => {
                setCurrentIndex(i);
                setIsFlipped(false);
              }}
              className={`h-2 w-2 rounded-full transition-all ${
                i === currentIndex ? 'bg-primary w-4' : 'bg-muted hover:bg-muted/80'
              }`}
            />
          ))}
        </div>

        <button
          onClick={goNext}
          disabled={currentIndex === cards.length - 1}
          className="flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium bg-primary text-primary-foreground hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          {t('nextCard')}
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
