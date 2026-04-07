import type { SlideData } from '@/types/presentation';
import type { SlideThemeConfig } from '../slide-themes';

interface Props {
  slide: SlideData;
  theme: SlideThemeConfig;
}

export function KeyTermsSlide({ slide, theme }: Props) {
  const terms = slide.terms || [];
  const useGrid = terms.length >= 4;

  return (
    <div
      className="absolute inset-0 bg-cover bg-center flex flex-col"
      style={{ backgroundImage: `url(${theme.bg.terms})` }}
    >
      {/* Title */}
      <div className="px-[7%] pt-[5%]">
        <h2 className={`${theme.headingColor} text-[2em] font-bold`}>
          {slide.title}
        </h2>
        <div className={`w-16 h-1 ${theme.badgeBg} rounded-full mt-2`} />
      </div>

      {/* Terms */}
      <div className={`flex-1 px-[7%] py-[3%] ${useGrid ? 'grid grid-cols-2 gap-[0.5em] content-center' : 'flex flex-col gap-[0.5em] justify-center'}`}>
        {terms.map((t, i) => (
          <div
            key={i}
            className={`${theme.cardBg} backdrop-blur-sm border-l-4 ${theme.accentBorder} rounded-lg shadow-sm px-[1em] py-[0.6em]`}
          >
            <div className={`${theme.accentColor} font-bold text-[0.9em]`}>
              {t.term}
            </div>
            <div className={`${theme.bodyColor} text-[0.8em] mt-[0.15em] leading-snug opacity-80`}>
              {t.definition}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
