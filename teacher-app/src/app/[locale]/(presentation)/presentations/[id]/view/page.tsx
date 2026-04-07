'use client';

import { useParams, useSearchParams } from 'next/navigation';
import { useRouter } from '@/i18n/routing';
import { SlideViewer } from '@/components/presentation/SlideViewer';
import { usePresentation } from '@/lib/hooks/use-presentations';
import { getTheme } from '@/components/presentation/slide-themes';
import type { PresentationData, PresentationContext } from '@/types/presentation';

export default function PresentationViewPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const presId = Number(params.id);
  const initialSlide = Number(searchParams.get('slide') || '0');
  const autoPrint = searchParams.get('print') === 'true';

  const { data: pres, isLoading } = usePresentation(presId || null);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="w-10 h-10 border-4 border-white/30 border-t-white rounded-full animate-spin" />
      </div>
    );
  }

  if (!pres) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <p className="text-white/60 text-lg">Презентация не найдена</p>
      </div>
    );
  }

  const slidesData = pres.slides_data as PresentationData;
  const contextData = pres.context_data as PresentationContext;
  const theme = getTheme(contextData.theme);

  return (
    <SlideViewer
      slides={slidesData.slides || []}
      theme={theme}
      context={{ subject: contextData.subject, grade_level: contextData.grade_level }}
      onExit={() => router.push(`/presentations/${presId}`)}
      initialSlide={initialSlide}
      autoPrint={autoPrint}
    />
  );
}
