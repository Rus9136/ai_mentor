import type { SlideData } from '@/types/presentation';
import type { SlideThemeConfig } from '../slide-themes';

interface Props {
  slide: SlideData;
  theme: SlideThemeConfig;
}

export function SummarySlide({ slide, theme }: Props) {
  const items = slide.items || [];

  return (
    <div className={`absolute inset-0 flex flex-col`}>
      {/* Top area with dark gradient */}
      <div className={`${theme.summaryHeaderBg} px-[6%] py-[4%]`}>
        <h2 className="text-white text-[1.8em] font-bold">{slide.title}</h2>
        <p className="text-white/60 text-[0.8em] mt-[0.3em] tracking-wide uppercase">
          Негізгі тұжырымдар
        </p>
      </div>

      {/* Items area with light background */}
      <div className={`flex-1 ${theme.slideBg} px-[6%] py-[3%] flex flex-col gap-[0.5em] justify-center`}>
        {items.map((item, i) => (
          <div key={i} className={`flex items-center gap-[0.8em] ${theme.cardBg} border ${theme.cardBorder} ${theme.cardShadow} rounded-xl px-[1.2em] py-[0.6em]`}>
            <div className="w-[1.6em] h-[1.6em] rounded-full bg-emerald-500 flex items-center justify-center shrink-0">
              <span className="text-white text-[0.7em] font-bold">&#10003;</span>
            </div>
            <span className={`${theme.headingColor} text-[0.9em] leading-snug`}>{item}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
