'use client';

import { Video, Trash2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { StatusBadge } from './status-badge';
import { MediaUploader, CompactMediaUploader } from './media-uploader';
import type { ParagraphContent } from '@/types';

interface VideoSectionProps {
  content: ParagraphContent | null | undefined;
  paragraphId: number;
  language: string;
  onUpload: (file: File) => void;
  onDelete: () => void;
  isUploading?: boolean;
  isDeleting?: boolean;
}

const VIDEO_ACCEPT = {
  'video/mp4': ['.mp4'],
  'video/webm': ['.webm'],
};

export function VideoSection({
  content,
  paragraphId,
  language,
  onUpload,
  onDelete,
  isUploading = false,
  isDeleting = false,
}: VideoSectionProps) {
  const hasVideo = !!content?.video_url;
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.ai-mentor.kz';

  // Build full video URL
  const videoUrl = content?.video_url
    ? content.video_url.startsWith('http')
      ? content.video_url
      : `${apiUrl}${content.video_url}`
    : null;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center gap-2">
          <Video className="h-5 w-5 text-muted-foreground" />
          <CardTitle className="text-lg">Видео</CardTitle>
        </div>
        <StatusBadge status={content?.status_video || 'empty'} />
      </CardHeader>
      <CardContent>
        {hasVideo && videoUrl ? (
          <div className="space-y-4">
            <div className="border rounded-lg overflow-hidden bg-black">
              <video controls className="w-full max-h-[400px]">
                <source src={videoUrl} type="video/mp4" />
                Ваш браузер не поддерживает воспроизведение видео.
              </video>
            </div>
            <div className="flex gap-2">
              <CompactMediaUploader
                accept={VIDEO_ACCEPT}
                maxSize={200 * 1024 * 1024}
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
            accept={VIDEO_ACCEPT}
            maxSize={200 * 1024 * 1024}
            onUpload={onUpload}
            isLoading={isUploading}
            label="Загрузить видео"
            description="MP4, WebM. Максимум 200 МБ."
          />
        )}
      </CardContent>
    </Card>
  );
}
