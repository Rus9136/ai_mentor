import type { SlideData } from '@/types/presentation';
import type { SlideThemeConfig } from '../slide-themes';

interface Props {
  slide: SlideData;
  theme: SlideThemeConfig;
}

const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F'];

export function QuizSlide({ slide, theme }: Props) {
  const options = slide.options || [];
  const answerIdx = slide.answer ?? -1;

  return (
    <div className={`absolute inset-0 ${theme.slideBg} flex flex-col`}>
      {/* Header with different accent */}
      <div className="bg-gradient-to-r from-emerald-600 to-teal-700 px-[6%] py-[2.5%]">
        <h2 className="text-white text-[1.6em] font-bold">{slide.title}</h2>
      </div>
      <div className="h-[3px] bg-emerald-400 w-[120px] ml-[6%]" />

      {/* Question card */}
      <div className="px-[6%] pt-[2.5%]">
        <div className={`${theme.cardBg} border ${theme.cardBorder} ${theme.cardShadow} rounded-xl p-[1.2em] border-l-4 border-l-emerald-500`}>
          <p className={`${theme.headingColor} text-[1.1em] font-semibold leading-snug`}>
            {slide.question}
          </p>
        </div>
      </div>

      {/* Options */}
      <div className="flex-1 px-[6%] py-[2%] flex flex-col gap-[0.4em] justify-center">
        {options.map((option, i) => {
          const isCorrect = i === answerIdx;
          const bg = isCorrect ? theme.correctBg : theme.optionBg;
          const border = isCorrect ? theme.correctBorder : theme.optionBorder;
          const textColor = isCorrect ? theme.correctText : theme.headingColor;

          return (
            <div
              key={i}
              className={`flex items-center gap-[0.8em] ${bg} border ${border} rounded-xl px-[1em] py-[0.55em] transition-colors`}
            >
              <span className={`${isCorrect ? 'bg-emerald-600 text-white' : `${theme.badgeBg} ${theme.badgeText}`} rounded-lg w-[1.8em] h-[1.8em] flex items-center justify-center text-[0.8em] font-bold shrink-0`}>
                {LETTERS[i] || i + 1}
              </span>
              <span className={`${textColor} text-[0.9em] flex-1 ${isCorrect ? 'font-semibold' : ''}`}>
                {option}
              </span>
              {isCorrect && (
                <span className="text-emerald-600 text-[1.1em]">&#10004;</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
