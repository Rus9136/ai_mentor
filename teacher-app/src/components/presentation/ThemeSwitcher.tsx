'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { Palette, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { THEMES } from './slide-themes';
import type { SlideThemeName } from '@/types/presentation';

const THEME_ORDER: SlideThemeName[] = [
  'warm', 'green', 'forest', 'midnight', 'parchment',
  'slate', 'electric', 'lavender', 'coral', 'ocean', 'sage',
];

interface ThemeSwitcherProps {
  currentTheme: SlideThemeName;
  onThemeChange: (theme: SlideThemeName) => void;
  isPending?: boolean;
  saved?: boolean;
}

export function ThemeSwitcher({
  currentTheme,
  onThemeChange,
  isPending,
  saved,
}: ThemeSwitcherProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Close on click-outside
  useEffect(() => {
    if (!open) return;
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [open]);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false);
    }
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [open]);

  const handleSelect = useCallback(
    (theme: SlideThemeName) => {
      if (theme === currentTheme) {
        setOpen(false);
        return;
      }
      onThemeChange(theme);
      setOpen(false);
    },
    [currentTheme, onThemeChange]
  );

  const themeLabel = THEMES[currentTheme]?.label ?? currentTheme;

  return (
    <div className="relative" ref={ref}>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setOpen((prev) => !prev)}
        className="gap-1.5"
        disabled={isPending}
      >
        <Palette className="h-4 w-4" />
        <span className="hidden sm:inline">
          {saved ? (
            <span className="flex items-center gap-1 text-green-600">
              <Check className="h-3 w-3" />
              Сохранено
            </span>
          ) : (
            themeLabel
          )}
        </span>
      </Button>

      {open && (
        <div className="absolute right-0 top-full z-50 mt-2 w-[340px] rounded-lg border bg-background p-3 shadow-lg">
          <p className="mb-2 text-xs font-medium text-muted-foreground">
            Тема оформления
          </p>
          <div className="grid grid-cols-3 gap-2">
            {THEME_ORDER.map((name) => {
              const theme = THEMES[name];
              const isActive = name === currentTheme;
              return (
                <button
                  key={name}
                  type="button"
                  onClick={() => handleSelect(name)}
                  className={`
                    group flex flex-col items-center gap-1 rounded-md p-1.5
                    transition-all duration-100
                    ${isActive
                      ? 'ring-2 ring-primary bg-primary/5'
                      : 'hover:bg-muted/50'}
                  `}
                >
                  <div
                    className="relative h-[48px] w-full rounded overflow-hidden"
                    style={{ backgroundColor: theme.bgColor.content }}
                  >
                    {/* Accent bar */}
                    <div
                      className="absolute top-0 left-0 h-1 w-2/5 rounded-br"
                      style={{ backgroundColor: theme.bgColor.summary }}
                    />
                    {/* Title placeholder */}
                    <div
                      className="absolute top-2.5 left-1/2 -translate-x-1/2 h-1.5 w-3/5 rounded-sm"
                      style={{ backgroundColor: theme.bgColor.summary }}
                    />
                    {/* Body lines */}
                    <div
                      className="absolute top-6 left-1/2 -translate-x-1/2 h-1 w-4/5 rounded-full"
                      style={{
                        backgroundColor: theme.bgColor.summary,
                        opacity: 0.25,
                      }}
                    />
                    {/* Active check */}
                    {isActive && (
                      <div className="absolute inset-0 flex items-center justify-center bg-black/10">
                        <Check className="h-4 w-4 text-white drop-shadow" />
                      </div>
                    )}
                  </div>
                  <span className="text-[10px] text-muted-foreground truncate max-w-full">
                    {theme.label}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
