'use client';

import { useState, useRef } from 'react';
import { useTranslations } from 'next-intl';
import { Button } from '@/components/ui/button';
import { Loader2 } from 'lucide-react';

interface QuizJoinScreenProps {
  onJoin: (code: string) => Promise<void>;
  initialCode?: string;
}

export default function QuizJoinScreen({ onJoin, initialCode }: QuizJoinScreenProps) {
  const t = useTranslations('quiz');
  const [digits, setDigits] = useState<string[]>(initialCode ? initialCode.split('') : Array(6).fill(''));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  const handleChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;
    const newDigits = [...digits];
    newDigits[index] = value.slice(-1);
    setDigits(newDigits);
    setError('');
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !digits[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (pasted.length > 0) {
      setDigits(pasted.split('').concat(Array(6 - pasted.length).fill('')));
    }
  };

  const handleSubmit = async () => {
    const code = digits.join('');
    if (code.length < 4) return;
    setLoading(true);
    setError('');
    try {
      await onJoin(code);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : t('invalidCode'));
    } finally {
      setLoading(false);
    }
  };

  const code = digits.join('');

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center px-4">
      <div className="w-full max-w-sm text-center">
        <h1 className="mb-8 text-2xl font-bold text-foreground">{t('enterCode')}</h1>

        <div className="mb-6 flex justify-center gap-2" onPaste={handlePaste}>
          {digits.map((digit, i) => (
            <input
              key={i}
              ref={(el) => { inputRefs.current[i] = el; }}
              type="text"
              inputMode="numeric"
              maxLength={1}
              value={digit}
              onChange={(e) => handleChange(i, e.target.value)}
              onKeyDown={(e) => handleKeyDown(i, e)}
              className="h-14 w-12 rounded-xl border-2 border-muted-foreground/30 bg-card text-center text-2xl font-bold text-foreground transition-colors focus:border-primary focus:outline-none"
              autoFocus={i === 0}
            />
          ))}
        </div>

        {error && <p className="mb-4 text-sm text-red-500">{error}</p>}

        <Button
          onClick={handleSubmit}
          disabled={code.length < 4 || loading}
          className="w-full rounded-xl py-6 text-lg font-semibold"
        >
          {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : t('join')}
        </Button>
      </div>
    </div>
  );
}
