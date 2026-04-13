import type { SlideData } from '@/types/presentation';
import type { SlideThemeConfig } from '../slide-themes';
import { getSlideBg } from '../slide-themes';

interface Props {
  slide: SlideData;
  theme: SlideThemeConfig;
}

export function ObjectivesSlide({ slide, theme }: Props) {
  const items = slide.items || [];

  return (
    <div
      className="absolute inset-0 bg-cover bg-center flex flex-col"
      style={getSlideBg(theme, 'content')}
    >
      {/* Eyebrow + Title */}
      <div className="px-[7%] pt-[4%]">
        <p className={`${theme.accentColor} text-[0.65em] font-bold uppercase tracking-wider`}>
          01
        </p>
        <h2 className={`${theme.headingColor} text-[2em] font-bold leading-tight mt-1`}>
          {slide.title}
        </h2>
      </div>

      {/* Items with numbered circles */}
      <div className="flex-1 px-[7%] py-[3%] flex flex-col justify-center gap-[0.5em]">
        {items.map((item, i) => (
          <div key={i} className="flex items-center gap-[0.7em]">
            <span className={`${theme.badgeBg} ${theme.badgeText} rounded-full min-w-[2em] h-[2em] flex items-center justify-center text-[0.8em] font-bold shrink-0`}>
              {i + 1}
            </span>
            <span className={`${theme.cardText || theme.headingColor} text-[0.95em] leading-snug`}>{item}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
