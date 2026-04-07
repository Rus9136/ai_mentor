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
    <div
      className="absolute inset-0 bg-cover bg-center flex flex-col"
      style={{ backgroundImage: `url(${theme.bg.content})` }}
    >
      {/* Title */}
      <div className="px-[7%] pt-[5%]">
        <h2 className={`${theme.headingColor} text-[2em] font-bold`}>
          {slide.title}
        </h2>
        <div className="w-16 h-1 bg-emerald-500 rounded-full mt-2" />
      </div>

      {/* Question */}
      <div className="px-[7%] pt-[2%]">
        <div className={`${theme.cardBg} backdrop-blur-sm border ${theme.cardBorder} border-l-4 border-l-emerald-500 rounded-xl p-[1em] shadow-sm`}>
          <p className={`${theme.cardText} text-[1.05em] font-semibold leading-snug`}>
            {slide.question}
          </p>
        </div>
      </div>

      {/* Options */}
      <div className="flex-1 px-[7%] py-[2%] flex flex-col gap-[0.35em] justify-center">
        {options.map((option, i) => {
          const isCorrect = i === answerIdx;
          const bg = isCorrect ? theme.correctBg : theme.optionBg;
          const border = isCorrect ? theme.correctBorder : theme.cardBorder;
          const textColor = isCorrect ? theme.correctText : theme.cardText;

          return (
            <div
              key={i}
              className={`flex items-center gap-[0.7em] ${bg} backdrop-blur-sm border ${border} rounded-xl px-[0.9em] py-[0.5em] shadow-sm`}
            >
              <span className={`${isCorrect ? 'bg-emerald-600 text-white' : `${theme.badgeBg} ${theme.badgeText}`} rounded-lg min-w-[1.7em] h-[1.7em] flex items-center justify-center text-[0.75em] font-bold shrink-0`}>
                {LETTERS[i]}
              </span>
              <span className={`${textColor} text-[0.85em] flex-1 ${isCorrect ? 'font-semibold' : ''}`}>
                {option}
              </span>
              {isCorrect && (
                <span className="text-emerald-600 text-[1em]">&#10004;</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
