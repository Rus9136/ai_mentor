import type { SlideData } from '@/types/presentation';
import type { SlideThemeConfig } from '../slide-themes';
import { getSlideBg } from '../slide-themes';
import { getMediaUrl } from '@/lib/api/client';

interface Props {
  slide: SlideData;
  theme: SlideThemeConfig;
}

export function ContentSlide({ slide, theme }: Props) {
  const layout = slide.layout_hint || 'image_left';

  if (layout === 'stat_callout' && slide.stat_value) {
    return <StatCalloutLayout slide={slide} theme={theme} />;
  }
  if (layout === 'image_right') {
    return <ImageLayout slide={slide} theme={theme} side="right" />;
  }
  return <ImageLayout slide={slide} theme={theme} side="left" />;
}

/** Image left or right + text on opposite side */
function ImageLayout({ slide, theme, side }: Props & { side: 'left' | 'right' }) {
  const imageUrl = slide.image_url ? getMediaUrl(slide.image_url) : null;

  return (
    <div
      className="absolute inset-0 bg-cover bg-center flex flex-col"
      style={getSlideBg(theme, 'content')}
    >
      {/* Eyebrow + Title */}
      <div className="px-[7%] pt-[4%]">
        <p className={`${theme.accentColor} text-[0.65em] font-bold uppercase tracking-wider`}>
          ТАҚЫРЫП
        </p>
        <h2 className={`${theme.headingColor} text-[1.8em] font-bold leading-tight mt-1`}>
          {slide.title}
        </h2>
        <div className={`w-12 h-[3px] ${theme.badgeBg} rounded-full mt-2`} />
      </div>

      {/* Body + Image */}
      <div className={`flex-1 px-[7%] py-[2%] flex ${side === 'right' ? 'flex-row' : 'flex-row-reverse'} gap-[3%] items-center`}>
        {/* Text side */}
        <div className="flex-[3]">
          <p className={`${theme.bodyColor} text-[0.95em] leading-[1.65] whitespace-pre-line`}>
            {slide.body}
          </p>
        </div>

        {/* Image side */}
        <div className="flex-[2]">
          {imageUrl ? (
            <div className="w-full rounded-xl overflow-hidden shadow-lg">
              <img src={imageUrl} alt={slide.title} className="w-full object-cover" loading="eager" />
            </div>
          ) : (
            <div className={`w-full aspect-[4/3] ${theme.badgeBg} rounded-xl flex items-center justify-center opacity-30`}>
              <div className={`w-[40%] aspect-square rounded-full ${theme.accentBg}`} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/** Big stat number + label + body text */
function StatCalloutLayout({ slide, theme }: Props) {
  return (
    <div
      className="absolute inset-0 bg-cover bg-center flex flex-col"
      style={getSlideBg(theme, 'content')}
    >
      {/* Eyebrow + Title */}
      <div className="px-[7%] pt-[4%]">
        <p className={`${theme.accentColor} text-[0.65em] font-bold uppercase tracking-wider`}>
          НЕГІЗГІ ФАКТ
        </p>
        <h2 className={`${theme.headingColor} text-[1.8em] font-bold leading-tight mt-1`}>
          {slide.title}
        </h2>
      </div>

      {/* Stat card + body */}
      <div className="flex-1 px-[7%] py-[2%] flex gap-[3%] items-center">
        {/* Stat card */}
        <div className={`flex-[2] ${theme.statBg} rounded-2xl flex flex-col items-center justify-center py-[3%] px-[2%] aspect-[4/3]`}>
          <span className={`${theme.statText} text-[3.5em] font-bold leading-none`}>
            {slide.stat_value}
          </span>
          {slide.stat_label && (
            <span className={`${theme.statLabel} text-[0.8em] mt-2 text-center leading-snug`}>
              {slide.stat_label}
            </span>
          )}
        </div>

        {/* Body text */}
        <div className="flex-[3]">
          <p className={`${theme.bodyColor} text-[0.95em] leading-[1.65] whitespace-pre-line`}>
            {slide.body}
          </p>
        </div>
      </div>
    </div>
  );
}
