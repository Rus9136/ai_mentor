import type { SlideData } from '@/types/presentation';
import type { SlideThemeConfig } from '../slide-themes';
import { getSlideBg } from '../slide-themes';

interface Props {
  slide: SlideData;
  theme: SlideThemeConfig;
}

const LETTERS = ['A', 'B', 'C', 'D'];

export function QuizSlide({ slide, theme }: Props) {
  const options = slide.options || [];

  return (
    <div
      className="absolute inset-0 bg-cover bg-center flex flex-col"
      style={getSlideBg(theme, 'content')}
    >
      {/* Eyebrow + Question */}
      <div className="px-[7%] pt-[4%]">
        <p className={`${theme.accentColor} text-[0.65em] font-bold uppercase tracking-wider`}>
          БІЛІМДІ ТЕКСЕР
        </p>
        <h2 className={`${theme.headingColor} text-[1.6em] font-bold leading-snug mt-1`}>
          {slide.question}
        </h2>
      </div>

      {/* 2x2 option grid */}
      <div className="flex-1 px-[7%] py-[3%] grid grid-cols-2 gap-[0.5em] content-center">
        {options.slice(0, 4).map((option, i) => (
          <div
            key={i}
            className={`${theme.cardBg} backdrop-blur-sm border ${theme.cardBorder} rounded-xl flex items-center gap-[0.6em] px-[0.8em] py-[0.6em] shadow-sm`}
          >
            {/* Letter badge */}
            <span className={`${theme.badgeBg} ${theme.badgeText} rounded-full min-w-[2em] h-[2em] flex items-center justify-center text-[0.75em] font-bold shrink-0`}>
              {LETTERS[i]}
            </span>
            <span className={`${theme.cardText} text-[0.85em] leading-snug`}>
              {option}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
