import type { SlideData } from '@/types/presentation';
import type { SlideThemeConfig } from '../slide-themes';

interface Props {
  slide: SlideData;
  theme: SlideThemeConfig;
}

export function SummarySlide({ slide, theme }: Props) {
  const items = slide.items || [];

  return (
    <div
      className="absolute inset-0 bg-cover bg-center flex flex-col"
      style={{ backgroundImage: `url(${theme.bg.summary})` }}
    >
      {/* Title */}
      <div className="px-[7%] pt-[6%]">
        <h2 className={`${theme.headingColor} text-[2.2em] font-bold`}>
          {slide.title}
        </h2>
        <p className={`${theme.bodyColor} opacity-60 text-[0.75em] mt-1 tracking-wide uppercase`}>
          Негізгі тұжырымдар
        </p>
      </div>

      {/* Items */}
      <div className="flex-1 px-[7%] py-[3%] flex flex-col gap-[0.45em] justify-center">
        {items.map((item, i) => (
          <div key={i} className={`flex items-center gap-[0.7em] ${theme.cardBg} backdrop-blur-sm border ${theme.cardBorder} rounded-xl px-[1em] py-[0.55em] shadow-sm`}>
            <div className={`${theme.checkBg} min-w-[1.5em] h-[1.5em] rounded-full flex items-center justify-center shrink-0`}>
              <span className="text-white text-[0.65em] font-bold">&#10003;</span>
            </div>
            <span className={`${theme.cardText} text-[0.88em] leading-snug`}>{item}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
