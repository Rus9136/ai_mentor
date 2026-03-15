'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';

interface QuizQuickAnswerProps {
  questionText: string;
  options: string[];
  onAnswer: (selectedOption: number) => void;
}

const OPTION_COLORS = [
  'bg-red-500 hover:bg-red-600',
  'bg-blue-500 hover:bg-blue-600',
  'bg-amber-500 hover:bg-amber-600',
  'bg-green-500 hover:bg-green-600',
  'bg-purple-500 hover:bg-purple-600',
  'bg-orange-500 hover:bg-orange-600',
];

const OPTION_LABELS = ['A', 'B', 'C', 'D', 'E', 'F'];

export default function QuizQuickAnswer({ questionText, options, onAnswer }: QuizQuickAnswerProps) {
  const [selected, setSelected] = useState<number | null>(null);

  const handleSelect = (index: number) => {
    if (selected !== null) return;
    setSelected(index);
    onAnswer(index);
  };

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center px-4 py-6">
      <h2 className="mb-8 text-center text-xl font-bold text-foreground">{questionText}</h2>

      <div className="w-full max-w-sm space-y-3">
        {options.map((option, i) => (
          <button
            key={i}
            onClick={() => handleSelect(i)}
            disabled={selected !== null}
            className={`w-full rounded-xl px-6 py-4 text-left text-white font-semibold transition-all ${
              selected === i ? 'ring-4 ring-white/50 scale-95' : ''
            } ${selected !== null && selected !== i ? 'opacity-40' : ''} ${OPTION_COLORS[i] || OPTION_COLORS[0]}`}
          >
            <span className="mr-3 font-bold">{OPTION_LABELS[i]}.</span>
            {option}
          </button>
        ))}
      </div>
    </div>
  );
}
