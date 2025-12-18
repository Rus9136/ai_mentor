'use client';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface LanguageSwitcherProps {
  value: 'ru' | 'kk';
  onChange: (value: 'ru' | 'kk') => void;
  className?: string;
}

export function LanguageSwitcher({ value, onChange, className }: LanguageSwitcherProps) {
  return (
    <div className={cn('flex gap-1 p-1 bg-muted rounded-lg', className)}>
      <Button
        variant={value === 'ru' ? 'default' : 'ghost'}
        size="sm"
        onClick={() => onChange('ru')}
        className="h-8"
      >
        Русский
      </Button>
      <Button
        variant={value === 'kk' ? 'default' : 'ghost'}
        size="sm"
        onClick={() => onChange('kk')}
        className="h-8"
      >
        Қазақша
      </Button>
    </div>
  );
}
