import type { SlideData } from '@/types/presentation';
import type { SlideThemeConfig } from '../slide-themes';

interface Props {
  slide: SlideData;
  theme: SlideThemeConfig;
}

export function ObjectivesSlide({ slide, theme }: Props) {
  const items = slide.items || [];

  return (
    <div className={`absolute inset-0 ${theme.slideBg} flex flex-col`}>
      {/* Header */}
      <div className={`${theme.headerBg} px-[6%] py-[2.5%] flex items-center gap-[1em]`}>
        <h2 className={`${theme.headerText} text-[1.6em] font-bold`}>{slide.title}</h2>
      </div>
      {/* Accent line */}
      <div className={`h-[3px] ${theme.headerAccent} w-[120px] ml-[6%]`} />

      {/* Items */}
      <div className="flex-1 px-[6%] py-[3%] flex flex-col justify-center gap-[0.6em]">
        {items.map((item, i) => (
          <div key={i} className={`flex items-start gap-[0.8em] ${theme.cardBg} ${theme.cardBorder} border ${theme.cardShadow} rounded-xl px-[1.2em] py-[0.7em]`}>
            <span className={`${theme.badgeBg} ${theme.badgeText} rounded-full w-[1.8em] h-[1.8em] flex items-center justify-center text-[0.85em] font-bold shrink-0 mt-[0.05em]`}>
              {i + 1}
            </span>
            <span className={`${theme.headingColor} text-[0.95em] leading-snug`}>{item}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
