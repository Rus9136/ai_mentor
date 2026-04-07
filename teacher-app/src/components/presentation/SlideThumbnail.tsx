'use client';

import { useRef, useState, useEffect } from 'react';
import type { SlideData } from '@/types/presentation';
import type { SlideThemeConfig } from './slide-themes';
import { SlideRenderer } from './SlideRenderer';

interface SlideThumbnailProps {
  slide: SlideData;
  theme: SlideThemeConfig;
  context?: { subject?: string; grade_level?: number };
  index?: number;
  onClick?: () => void;
}

const RENDER_W = 960;
const RENDER_H = 540;

export function SlideThumbnail({ slide, theme, context, index, onClick }: SlideThumbnailProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(0.3);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const obs = new ResizeObserver(([entry]) => {
      setScale(entry.contentRect.width / RENDER_W);
    });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  return (
    <div
      ref={containerRef}
      className={`w-full aspect-video overflow-hidden rounded-lg border border-slate-200 bg-slate-100 relative ${onClick ? 'cursor-pointer hover:ring-2 hover:ring-blue-400 transition-shadow' : ''}`}
      onClick={onClick}
    >
      <div
        className="origin-top-left"
        style={{
          width: RENDER_W,
          height: RENDER_H,
          transform: `scale(${scale})`,
        }}
      >
        <SlideRenderer slide={slide} theme={theme} context={context} className="w-full h-full" />
      </div>
      {index !== undefined && (
        <div className="absolute top-1 left-1 bg-black/50 text-white text-[10px] px-1.5 py-0.5 rounded font-medium">
          {index + 1}
        </div>
      )}
    </div>
  );
}
