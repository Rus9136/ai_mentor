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
    <div
      className="absolute inset-0 bg-cover bg-center flex flex-col"
      style={{ backgroundImage: `url(${theme.bg.content})` }}
    >
      {/* Title */}
      <div className="px-[7%] pt-[5%]">
        <h2 className={`${theme.headingColor} text-[2em] font-bold`}>
          {slide.title}
        </h2>
        <div className={`w-16 h-1 ${theme.badgeBg} rounded-full mt-2`} />
      </div>

      {/* Body */}
      <div className={`flex-1 px-[7%] py-[2.5%] flex ${imageUrl ? 'gap-[3%]' : ''} items-start`}>
        <div className={imageUrl ? 'flex-[3]' : 'flex-1 max-w-[75%]'}>
          <div className={`${theme.cardBg} backdrop-blur-sm border ${theme.cardBorder} rounded-xl p-[1.2em] shadow-sm`}>
            <p className={`${theme.cardText} text-[1.05em] leading-[1.7] whitespace-pre-line`}>
              {slide.body}
            </p>
          </div>
        </div>

        {imageUrl && (
          <div className="flex-[2] flex items-start">
            <div className="w-full rounded-xl overflow-hidden shadow-lg border border-white/30">
              <img
                src={imageUrl}
                alt={slide.title}
                className="w-full h-full object-contain"
                loading="eager"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
