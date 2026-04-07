import type { SlideData } from '@/types/presentation';
import type { SlideThemeConfig } from '../slide-themes';

interface Props {
  slide: SlideData;
  theme: SlideThemeConfig;
}

export function ObjectivesSlide({ slide, theme }: Props) {
  const items = slide.items || [];

  return (
    <div
      className="absolute inset-0 bg-cover bg-center flex flex-col"
      style={{ backgroundImage: `url(${theme.bg.content})` }}
    >
      {/* Title */}
      <div className="px-[7%] pt-[5%]">
        <h2 className={`${theme.headingColor} text-[2em] font-bold`}>
          {slide.title}
        </h2>
        <div className={`w-16 h-1 ${theme.badgeBg} rounded-full mt-2`} />
      </div>

      {/* Items */}
      <div className="flex-1 px-[7%] py-[3%] flex flex-col justify-center gap-[0.5em]">
        {items.map((item, i) => (
          <div key={i} className={`flex items-start gap-[0.7em] ${theme.cardBg} backdrop-blur-sm border ${theme.cardBorder} rounded-xl px-[1em] py-[0.6em] shadow-sm`}>
            <span className={`${theme.badgeBg} ${theme.badgeText} rounded-full min-w-[1.7em] h-[1.7em] flex items-center justify-center text-[0.8em] font-bold shrink-0`}>
              {i + 1}
            </span>
            <span className={`${theme.cardText} text-[0.9em] leading-snug`}>{item}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
