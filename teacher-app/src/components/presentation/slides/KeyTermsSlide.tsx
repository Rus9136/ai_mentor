import type { SlideData } from '@/types/presentation';
import type { SlideThemeConfig } from '../slide-themes';
import { getSlideBg } from '../slide-themes';

interface Props {
  slide: SlideData;
  theme: SlideThemeConfig;
}

export function KeyTermsSlide({ slide, theme }: Props) {
  const terms = slide.terms || [];
  const cols = terms.length >= 4 ? 3 : 2;

  return (
    <div
      className="absolute inset-0 bg-cover bg-center flex flex-col"
      style={getSlideBg(theme, 'terms')}
    >
      {/* Eyebrow + Title */}
      <div className="px-[7%] pt-[4%]">
        <p className={`${theme.accentColor} text-[0.65em] font-bold uppercase tracking-wider`}>
          ТЕРМИНДЕР
        </p>
        <h2 className={`${theme.headingColor} text-[1.8em] font-bold leading-tight mt-1`}>
          {slide.title}
        </h2>
      </div>

      {/* Card grid */}
      <div className={`flex-1 px-[7%] py-[3%] grid gap-[0.5em] content-center`}
        style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}
      >
        {terms.map((t, i) => (
          <div
            key={i}
            className={`${theme.cardBg} backdrop-blur-sm border ${theme.cardBorder} rounded-xl overflow-hidden shadow-sm`}
          >
            {/* Top accent strip */}
            <div className={`h-[3px] ${theme.badgeBg}`} />
            <div className="px-[0.8em] py-[0.6em]">
              <div className={`${theme.accentColor} font-bold text-[0.85em]`}>
                {t.term}
              </div>
              <div className={`${theme.bodyColor} text-[0.7em] mt-[0.2em] leading-snug opacity-80`}>
                {t.definition}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
