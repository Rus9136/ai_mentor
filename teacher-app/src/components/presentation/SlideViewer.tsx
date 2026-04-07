'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { ChevronLeft, ChevronRight, X, Maximize, Minimize, Printer } from 'lucide-react';
import type { SlideData } from '@/types/presentation';
import type { SlideThemeConfig } from './slide-themes';
import { SlideRenderer } from './SlideRenderer';
import { useSlideKeyboard } from '@/lib/hooks/use-slide-keyboard';

interface SlideViewerProps {
  slides: SlideData[];
  theme: SlideThemeConfig;
  context?: { subject?: string; grade_level?: number };
  onExit?: () => void;
  initialSlide?: number;
  autoPrint?: boolean;
}

export function SlideViewer({ slides, theme, context, onExit, initialSlide = 0, autoPrint = false }: SlideViewerProps) {
  const [current, setCurrent] = useState(initialSlide);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const [printing, setPrinting] = useState(false);
  const hideTimerRef = useRef<NodeJS.Timeout | null>(null);

  const total = slides.length;

  // Keyboard navigation
  useSlideKeyboard({
    totalSlides: total,
    currentSlide: current,
    setCurrentSlide: setCurrent,
    onExit,
    onPrint: handlePrint,
  });

  // Track fullscreen state
  useEffect(() => {
    const onChange = () => setIsFullscreen(!!document.fullscreenElement);
    document.addEventListener('fullscreenchange', onChange);
    return () => document.removeEventListener('fullscreenchange', onChange);
  }, []);

  // Auto-hide controls
  const resetHideTimer = useCallback(() => {
    setShowControls(true);
    if (hideTimerRef.current) clearTimeout(hideTimerRef.current);
    hideTimerRef.current = setTimeout(() => setShowControls(false), 3000);
  }, []);

  useEffect(() => {
    resetHideTimer();
    return () => { if (hideTimerRef.current) clearTimeout(hideTimerRef.current); };
  }, [resetHideTimer]);

  // Auto-print mode
  useEffect(() => {
    if (autoPrint) {
      const timer = setTimeout(() => handlePrint(), 500);
      return () => clearTimeout(timer);
    }
  }, [autoPrint]);

  function handlePrint() {
    setPrinting(true);
    // Wait for all slides to render
    setTimeout(() => {
      window.print();
      // Reset after print
      const reset = () => setPrinting(false);
      window.addEventListener('afterprint', reset, { once: true });
      // Fallback reset
      setTimeout(reset, 5000);
    }, 300);
  }

  function toggleFullscreen() {
    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      document.documentElement.requestFullscreen().catch(() => {});
    }
  }

  const goNext = () => setCurrent((p) => Math.min(p + 1, total - 1));
  const goPrev = () => setCurrent((p) => Math.max(p - 1, 0));

  return (
    <div
      className="fixed inset-0 bg-black flex flex-col items-center justify-center z-50"
      onMouseMove={resetHideTimer}
    >
      {/* Print area: all slides (hidden until printing) */}
      {printing && (
        <div className="slide-print-area">
          {slides.map((slide, i) => (
            <div key={i} className="slide-print-page">
              <div className="w-[100vw] h-[100vh]">
                <SlideRenderer slide={slide} theme={theme} context={context} className="w-full h-full" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Current slide (hidden during print) */}
      <div className="no-print w-full h-full flex items-center justify-center p-2 sm:p-4">
        <div className="w-full max-w-[1400px] max-h-full aspect-video relative">
          <SlideRenderer
            slide={slides[current]}
            theme={theme}
            context={context}
            className="w-full h-full rounded-lg shadow-2xl"
          />

          {/* Click zones */}
          <div className="absolute inset-y-0 left-0 w-[20%] cursor-pointer z-10" onClick={goPrev} />
          <div className="absolute inset-y-0 right-0 w-[20%] cursor-pointer z-10" onClick={goNext} />
        </div>
      </div>

      {/* Controls bar */}
      <div
        className={`no-print absolute bottom-0 left-0 right-0 bg-black/60 backdrop-blur-sm transition-opacity duration-300 ${showControls ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
      >
        <div className="flex items-center justify-between px-4 py-2 max-w-[1400px] mx-auto">
          {/* Left: exit */}
          <button
            onClick={onExit}
            className="text-white/80 hover:text-white p-2 rounded-lg hover:bg-white/10 transition-colors"
            title="Выйти"
          >
            <X className="w-5 h-5" />
          </button>

          {/* Center: navigation */}
          <div className="flex items-center gap-3">
            <button
              onClick={goPrev}
              disabled={current === 0}
              className="text-white/80 hover:text-white p-2 rounded-lg hover:bg-white/10 disabled:opacity-30 transition-colors"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <span className="text-white/90 text-sm font-medium min-w-[60px] text-center tabular-nums">
              {current + 1} / {total}
            </span>
            <button
              onClick={goNext}
              disabled={current === total - 1}
              className="text-white/80 hover:text-white p-2 rounded-lg hover:bg-white/10 disabled:opacity-30 transition-colors"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>

          {/* Right: fullscreen + print */}
          <div className="flex items-center gap-1">
            <button
              onClick={handlePrint}
              className="text-white/80 hover:text-white p-2 rounded-lg hover:bg-white/10 transition-colors"
              title="Скачать PDF"
            >
              <Printer className="w-5 h-5" />
            </button>
            <button
              onClick={toggleFullscreen}
              className="text-white/80 hover:text-white p-2 rounded-lg hover:bg-white/10 transition-colors"
              title="Полный экран"
            >
              {isFullscreen ? <Minimize className="w-5 h-5" /> : <Maximize className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
