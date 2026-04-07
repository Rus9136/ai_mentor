import type { SlideData } from '@/types/presentation';
import type { SlideThemeConfig } from './slide-themes';
import { TitleSlide } from './slides/TitleSlide';
import { ObjectivesSlide } from './slides/ObjectivesSlide';
import { ContentSlide } from './slides/ContentSlide';
import { KeyTermsSlide } from './slides/KeyTermsSlide';
import { QuizSlide } from './slides/QuizSlide';
import { SummarySlide } from './slides/SummarySlide';

interface SlideRendererProps {
  slide: SlideData;
  theme: SlideThemeConfig;
  context?: { subject?: string; grade_level?: number };
  className?: string;
}

const SLIDE_COMPONENTS: Record<string, React.ComponentType<{ slide: SlideData; theme: SlideThemeConfig; context?: SlideRendererProps['context'] }>> = {
  title: TitleSlide,
  objectives: ObjectivesSlide,
  content: ContentSlide,
  key_terms: KeyTermsSlide,
  quiz: QuizSlide,
  summary: SummarySlide,
};

export function SlideRenderer({ slide, theme, context, className = '' }: SlideRendererProps) {
  const Component = SLIDE_COMPONENTS[slide.type] || ContentSlide;

  return (
    <div className={`aspect-video relative overflow-hidden select-none ${className}`}>
      <Component slide={slide} theme={theme} context={context} />
    </div>
  );
}
