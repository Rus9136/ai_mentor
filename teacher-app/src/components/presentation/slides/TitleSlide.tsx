import type { SlideData } from '@/types/presentation';
import type { SlideThemeConfig } from '../slide-themes';
import { getSlideBg } from '../slide-themes';

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
    <div
      className="absolute inset-0 bg-cover bg-center flex flex-col items-start justify-center"
      style={getSlideBg(theme, 'title')}
    >
      <div className="px-[7%] py-[5%] max-w-[65%]">
        <p className={`${theme.accentColor} text-[0.65em] font-bold uppercase tracking-wider mb-2`}>
          САБАҚ
        </p>
        <h1 className={`${theme.titleColor} text-[3em] font-extrabold leading-[1.1] drop-shadow-sm`}>
          {slide.title}
        </h1>
        <div className={`w-14 h-1 ${theme.badgeBg} rounded-full mt-3`} />
        {slide.subtitle && (
          <p className={`${theme.subtitleColor} text-[1.2em] mt-[0.6em] leading-snug`}>
            {slide.subtitle}
          </p>
        )}
        {footer && (
          <p className={`${theme.subtitleColor} text-[0.8em] mt-[1.5em] opacity-70 tracking-wide`}>
            {footer}
          </p>
        )}
      </div>
    </div>
  );
}
