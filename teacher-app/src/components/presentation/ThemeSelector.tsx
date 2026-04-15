'use client';

import { THEMES } from './slide-themes';
import type { SlideThemeName } from '@/types/presentation';

const THEME_ORDER: SlideThemeName[] = [
  'warm', 'green', 'forest', 'midnight', 'parchment',
  'slate', 'electric', 'lavender', 'coral', 'ocean', 'sage',
];

interface ThemeSelectorProps {
  value: SlideThemeName | null;
  onChange: (theme: SlideThemeName) => void;
  autoSelectedTheme: SlideThemeName | null;
  disabled?: boolean;
  labels: { heading: string; auto: string };
}

export function ThemeSelector({
  value,
  onChange,
  autoSelectedTheme,
  disabled,
  labels,
}: ThemeSelectorProps) {
  const activeTheme = value ?? autoSelectedTheme;
  const isAuto = value === null && autoSelectedTheme !== null;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">{labels.heading}</span>
        {activeTheme && (
          <span className="text-xs text-muted-foreground">
            {THEMES[activeTheme].label}
          </span>
        )}
      </div>

      <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-thin">
        {THEME_ORDER.map((name) => {
          const theme = THEMES[name];
          const isSelected = activeTheme === name;
          const showAuto = isAuto && isSelected;

          return (
            <button
              key={name}
              type="button"
              disabled={disabled}
              onClick={() => onChange(name)}
              className="group flex flex-col items-center gap-1 flex-shrink-0"
            >
              {/* Card */}
              <div
                className={`
                  relative w-[144px] h-[81px] rounded-md overflow-hidden
                  transition-all duration-150
                  ${isSelected
                    ? 'ring-2 ring-primary'
                    : 'ring-1 ring-transparent group-hover:ring-primary/30'}
                  ${!disabled ? 'cursor-pointer group-hover:scale-[1.02]' : 'opacity-60'}
                `}
                style={{ backgroundColor: theme.bgColor.content }}
              >
                {/* Auto badge */}
                {showAuto && (
                  <span className="absolute top-1 right-1 text-[9px] bg-black/20 text-white px-1 rounded">
                    {labels.auto}
                  </span>
                )}

                {/* Primary accent bar — top-left */}
                <div
                  className="absolute top-0 left-0 h-1 rounded-br"
                  style={{
                    width: '40%',
                    backgroundColor: theme.bgColor.summary,
                  }}
                />

                {/* Title placeholder */}
                <div
                  className="absolute top-3 left-1/2 -translate-x-1/2 h-2 rounded-sm"
                  style={{
                    width: '60%',
                    backgroundColor: theme.bgColor.summary,
                  }}
                />

                {/* Body line placeholders */}
                <div className="absolute top-8 left-1/2 -translate-x-1/2 space-y-1" style={{ width: '70%' }}>
                  <div className="h-[3px] rounded-full w-full" style={{ backgroundColor: theme.bgColor.summary, opacity: 0.25 }} />
                  <div className="h-[3px] rounded-full w-[80%]" style={{ backgroundColor: theme.bgColor.summary, opacity: 0.2 }} />
                </div>

                {/* Accent circle — bottom-right */}
                <div
                  className="absolute bottom-2 right-2 w-3 h-3 rounded-full"
                  style={{ backgroundColor: theme.bgColor.summary, opacity: 0.6 }}
                />
              </div>

              {/* Label */}
              <span className="flex items-center gap-1 text-xs text-muted-foreground max-w-[144px] truncate">
                {isSelected && (
                  <svg className="w-3 h-3 text-primary flex-shrink-0" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0zm3.78 5.22a.75.75 0 0 0-1.06 0L7 8.94 5.28 7.22a.75.75 0 1 0-1.06 1.06l2.25 2.25a.75.75 0 0 0 1.06 0l4.25-4.25a.75.75 0 0 0 0-1.06z" />
                  </svg>
                )}
                {theme.label.length > 14 ? theme.label.slice(0, 14) + '...' : theme.label}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
