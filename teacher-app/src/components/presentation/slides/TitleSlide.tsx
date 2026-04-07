import type { SlideData } from '@/types/presentation';
import type { SlideThemeConfig } from '../slide-themes';

interface Props {
  slide: SlideData;
  theme: SlideThemeConfig;
  context?: { subject?: string; grade_level?: number };
}

export function TitleSlide({ slide, theme, context }: Props) {
  const subject = context?.subject || '';
  const grade = context?.grade_level;
  const footer = grade ? `${subject}  •  ${grade} класс` : subject;

  return (
    <div className={`absolute inset-0 ${theme.titleGradient} flex flex-col items-center justify-center p-[8%]`}>
      {/* Decorative elements */}
      <div className={`absolute top-0 left-0 w-full h-1 ${theme.headerAccent}`} />
      <div className={`absolute top-[15%] right-[10%] w-[200px] h-[200px] rounded-full ${theme.titleDecor} blur-3xl`} />
      <div className={`absolute bottom-[20%] left-[5%] w-[150px] h-[150px] rounded-full ${theme.titleDecor} blur-2xl`} />

      {/* Title */}
      <h1 className={`${theme.titleText} text-[2.8em] font-bold text-center leading-tight max-w-[85%] z-10`}>
        {slide.title}
      </h1>

      {/* Subtitle */}
      {slide.subtitle && (
        <p className={`${theme.titleSubtext} text-[1.3em] text-center mt-[0.8em] max-w-[75%] z-10`}>
          {slide.subtitle}
        </p>
      )}

      {/* Footer bar */}
      {footer && (
        <div className="absolute bottom-0 left-0 w-full bg-black/20 py-[0.6em] px-[4%]">
          <p className={`${theme.titleSubtext} text-[0.75em] text-center tracking-wider uppercase`}>
            {footer}
          </p>
        </div>
      )}
    </div>
  );
}
