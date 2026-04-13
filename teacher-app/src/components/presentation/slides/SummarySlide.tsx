import type { SlideData } from '@/types/presentation';
import type { SlideThemeConfig } from '../slide-themes';
import { getSlideBg } from '../slide-themes';

interface Props {
  slide: SlideData;
  theme: SlideThemeConfig;
}

export function SummarySlide({ slide, theme }: Props) {
  const items = slide.items || [];

  return (
    <div
      className="absolute inset-0 bg-cover bg-center flex flex-col"
      style={getSlideBg(theme, 'summary')}
    >
      {/* Title on colored background */}
      <div className="px-[7%] pt-[5%]">
        <p className="text-white/80 text-[0.65em] font-bold uppercase tracking-wider">
          ҚОРЫТЫНДЫ
        </p>
        <h2 className="text-white text-[2.4em] font-bold leading-tight mt-1">
          {slide.title}
        </h2>
      </div>

      {/* Items as cards on colored background */}
      <div className="flex-1 px-[7%] py-[3%] flex flex-col gap-[0.4em] justify-center">
        {items.map((item, i) => (
          <div key={i} className={`flex items-center gap-[0.7em] ${theme.cardBg} backdrop-blur-sm rounded-xl px-[1em] py-[0.5em] shadow-sm`}>
            <div className={`${theme.checkBg} min-w-[1.5em] h-[1.5em] rounded-full flex items-center justify-center shrink-0`}>
              <span className="text-white text-[0.6em] font-bold">&#10003;</span>
            </div>
            <span className={`${theme.cardText} text-[0.85em] leading-snug`}>{item}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
