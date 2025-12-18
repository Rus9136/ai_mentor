'use client';

import { Presentation, Trash2, ExternalLink } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { StatusBadge } from './status-badge';
import { MediaUploader, CompactMediaUploader } from './media-uploader';
import type { ParagraphContent } from '@/types';

interface SlidesSectionProps {
  content: ParagraphContent | null | undefined;
  paragraphId: number;
  language: string;
  onUpload: (file: File) => void;
  onDelete: () => void;
  isUploading?: boolean;
  isDeleting?: boolean;
}

const SLIDES_ACCEPT = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
};

export function SlidesSection({
  content,
  paragraphId,
  language,
  onUpload,
  onDelete,
  isUploading = false,
  isDeleting = false,
}: SlidesSectionProps) {
  const hasSlides = !!content?.slides_url;
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.ai-mentor.kz';

  // Build full slides URL
  const slidesUrl = content?.slides_url
    ? content.slides_url.startsWith('http')
      ? content.slides_url
      : `${apiUrl}${content.slides_url}`
    : null;

  const isPdf = slidesUrl?.toLowerCase().endsWith('.pdf');

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center gap-2">
          <Presentation className="h-5 w-5 text-muted-foreground" />
          <CardTitle className="text-lg">Слайды</CardTitle>
        </div>
        <StatusBadge status={content?.status_slides || 'empty'} />
      </CardHeader>
      <CardContent>
        {hasSlides && slidesUrl ? (
          <div className="space-y-4">
            {isPdf ? (
              <div className="border rounded-lg overflow-hidden">
                <iframe
                  src={slidesUrl}
                  className="w-full h-[400px]"
                  title="PDF Слайды"
                />
              </div>
            ) : (
              <div className="flex items-center gap-2 p-4 bg-muted rounded-lg">
                <Presentation className="h-8 w-8 text-muted-foreground" />
                <div className="flex-1">
                  <p className="font-medium">Презентация PPTX</p>
                  <p className="text-sm text-muted-foreground">
                    Файл загружен. Скачайте для просмотра.
                  </p>
                </div>
                <Button variant="outline" size="sm" asChild>
                  <a href={slidesUrl} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="h-4 w-4 mr-2" />
                    Открыть
                  </a>
                </Button>
              </div>
            )}
            <div className="flex gap-2">
              <CompactMediaUploader
                accept={SLIDES_ACCEPT}
                maxSize={50 * 1024 * 1024}
                onUpload={onUpload}
                isLoading={isUploading}
                label="Заменить"
              />
              <Button
                variant="destructive"
                size="sm"
                onClick={onDelete}
                disabled={isDeleting}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Удалить
              </Button>
            </div>
          </div>
        ) : (
          <MediaUploader
            accept={SLIDES_ACCEPT}
            maxSize={50 * 1024 * 1024}
            onUpload={onUpload}
            isLoading={isUploading}
            label="Загрузить слайды"
            description="PDF, PPTX. Максимум 50 МБ."
          />
        )}
      </CardContent>
    </Card>
  );
}
