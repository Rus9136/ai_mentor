import type { SlideData } from '@/types/presentation';
import type { SlideThemeConfig } from '../slide-themes';

interface Props {
  slide: SlideData;
  theme: SlideThemeConfig;
}

export function KeyTermsSlide({ slide, theme }: Props) {
  const terms = slide.terms || [];
  const isGrid = terms.length >= 4;

  return (
    <div className={`absolute inset-0 ${theme.slideBg} flex flex-col`}>
      {/* Header */}
      <div className={`${theme.headerBg} px-[6%] py-[2.5%]`}>
        <h2 className={`${theme.headerText} text-[1.6em] font-bold`}>{slide.title}</h2>
      </div>
      <div className={`h-[3px] ${theme.headerAccent} w-[120px] ml-[6%]`} />

      {/* Terms */}
      <div className={`flex-1 px-[6%] py-[3%] ${isGrid ? 'grid grid-cols-2 gap-[0.6em] content-start' : 'flex flex-col gap-[0.6em] justify-center'}`}>
        {terms.map((t, i) => (
          <div
            key={i}
            className={`${theme.cardBg} border-l-4 ${theme.accentBorder} rounded-lg ${theme.cardShadow} px-[1.2em] py-[0.7em]`}
          >
            <div className={`${theme.accentColor} font-semibold text-[0.9em]`}>
              {t.term}
            </div>
            <div className={`${theme.bodyColor} text-[0.8em] mt-[0.2em] leading-snug`}>
              {t.definition}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
