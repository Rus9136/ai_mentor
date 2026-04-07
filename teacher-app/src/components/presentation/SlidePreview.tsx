'use client';

import type { SlideData } from '@/types/presentation';
import type { SlideThemeConfig } from './slide-themes';
import { SlideThumbnail } from './SlideThumbnail';

interface SlidePreviewProps {
  slides: SlideData[];
  theme: SlideThemeConfig;
  context?: { subject?: string; grade_level?: number };
  onSlideClick?: (index: number) => void;
}

export function SlidePreview({ slides, theme, context, onSlideClick }: SlidePreviewProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
      {slides.map((slide, idx) => (
        <SlideThumbnail
          key={idx}
          slide={slide}
          theme={theme}
          context={context}
          index={idx}
          onClick={onSlideClick ? () => onSlideClick(idx) : undefined}
        />
      ))}
    </div>
  );
}
