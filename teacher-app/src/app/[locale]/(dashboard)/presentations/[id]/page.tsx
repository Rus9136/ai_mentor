'use client';

import { useParams } from 'next/navigation';
import { useRouter } from '@/i18n/routing';
import { ArrowLeft, Download, Trash2, Play, FileDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { SlidePreview } from '@/components/presentation/SlidePreview';
import { usePresentation, useDeletePresentation } from '@/lib/hooks/use-presentations';
import { exportPresentationPptx } from '@/lib/api/presentations';
import { getTheme } from '@/components/presentation/slide-themes';
import type { PresentationData, PresentationContext } from '@/types/presentation';

export default function PresentationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const presId = Number(params.id);

  const { data: pres, isLoading } = usePresentation(presId || null);
  const deleteMutation = useDeletePresentation();

  const handleDelete = () => {
    if (!confirm('Удалить эту презентацию?')) return;
    deleteMutation.mutate(presId, {
      onSuccess: () => router.push('/presentations'),
    });
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!pres) {
    return (
      <div className="py-16 text-center text-muted-foreground">
        Презентация не найдена
      </div>
    );
  }

  const slidesData = pres.slides_data as PresentationData;
  const contextData = pres.context_data as PresentationContext;
  const theme = getTheme(contextData.theme);

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => router.push('/presentations')}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">{pres.title}</h1>
            <p className="text-sm text-muted-foreground">
              {contextData.subject} {contextData.grade_level}-сынып | {pres.language === 'kk' ? 'QAZ' : 'RUS'} | {pres.slide_count} слайдов
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => router.push(`/presentations/${presId}/view`)}>
            <Play className="mr-2 h-4 w-4" />
            Начать показ
          </Button>
          <Button variant="outline" onClick={() => router.push(`/presentations/${presId}/view?print=true`)}>
            <FileDown className="mr-2 h-4 w-4" />
            PDF
          </Button>
          <Button variant="outline" onClick={() => exportPresentationPptx(presId, contextData.theme || 'blue')}>
            <Download className="mr-2 h-4 w-4" />
            PPTX
          </Button>
          <Button variant="destructive" onClick={handleDelete}>
            <Trash2 className="mr-2 h-4 w-4" />
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">
            {slidesData.title} — {slidesData.slides?.length || 0} слайдов
          </CardTitle>
        </CardHeader>
        <CardContent>
          <SlidePreview
            slides={slidesData.slides || []}
            theme={theme}
            context={{ subject: contextData.subject, grade_level: contextData.grade_level }}
            onSlideClick={(idx) => router.push(`/presentations/${presId}/view?slide=${idx}`)}
          />
        </CardContent>
      </Card>
    </div>
  );
}
