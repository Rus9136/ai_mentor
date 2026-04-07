import type { SlideData } from '@/types/presentation';
import type { SlideThemeConfig } from '../slide-themes';
import { getMediaUrl } from '@/lib/api/client';

interface Props {
  slide: SlideData;
  theme: SlideThemeConfig;
}

export function ContentSlide({ slide, theme }: Props) {
  const imageUrl = slide.image_url ? getMediaUrl(slide.image_url) : null;

  return (
    <div className={`absolute inset-0 ${theme.slideBg} flex flex-col`}>
      {/* Header */}
      <div className={`${theme.headerBg} px-[6%] py-[2.5%]`}>
        <h2 className={`${theme.headerText} text-[1.6em] font-bold`}>{slide.title}</h2>
      </div>
      <div className={`h-[3px] ${theme.headerAccent} w-[120px] ml-[6%]`} />

      {/* Body */}
      <div className={`flex-1 px-[6%] py-[3%] flex ${imageUrl ? 'gap-[4%]' : ''}`}>
        {/* Text */}
        <div className={imageUrl ? 'flex-[3]' : 'flex-1'}>
          <div className={`${theme.cardBg} border ${theme.cardBorder} ${theme.cardShadow} rounded-xl p-[1.5em] h-full`}>
            <p className={`${theme.bodyColor} text-[0.95em] leading-relaxed whitespace-pre-line`}>
              {slide.body}
            </p>
          </div>
        </div>

        {/* Image */}
        {imageUrl && (
          <div className="flex-[2] flex items-start">
            <div className={`w-full rounded-xl overflow-hidden ${theme.cardShadow} border ${theme.cardBorder}`}>
              <img
                src={imageUrl}
                alt={slide.title}
                className="w-full h-full object-contain max-h-[60vh]"
                loading="eager"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
