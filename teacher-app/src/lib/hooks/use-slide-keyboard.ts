import { useEffect } from 'react';

interface UseSlideKeyboardOptions {
  totalSlides: number;
  currentSlide: number;
  setCurrentSlide: (n: number | ((prev: number) => number)) => void;
  onExit?: () => void;
  onPrint?: () => void;
}

export function useSlideKeyboard({
  totalSlides,
  currentSlide,
  setCurrentSlide,
  onExit,
  onPrint,
}: UseSlideKeyboardOptions) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowRight':
        case 'ArrowDown':
        case ' ':
        case 'PageDown':
          e.preventDefault();
          setCurrentSlide((prev: number) => Math.min(prev + 1, totalSlides - 1));
          break;

        case 'ArrowLeft':
        case 'ArrowUp':
        case 'PageUp':
          e.preventDefault();
          setCurrentSlide((prev: number) => Math.max(prev - 1, 0));
          break;

        case 'Home':
          e.preventDefault();
          setCurrentSlide(0);
          break;

        case 'End':
          e.preventDefault();
          setCurrentSlide(totalSlides - 1);
          break;

        case 'Escape':
          if (document.fullscreenElement) {
            document.exitFullscreen();
          } else if (onExit) {
            onExit();
          }
          break;

        case 'F11':
          e.preventDefault();
          if (document.fullscreenElement) {
            document.exitFullscreen();
          } else {
            document.documentElement.requestFullscreen().catch(() => {});
          }
          break;

        case 'p':
        case 'P':
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            onPrint?.();
          }
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [totalSlides, currentSlide, setCurrentSlide, onExit, onPrint]);
}
