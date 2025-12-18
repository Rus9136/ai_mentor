'use client';

import { Headphones, Trash2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { StatusBadge } from './status-badge';
import { MediaUploader, CompactMediaUploader } from './media-uploader';
import type { ParagraphContent } from '@/types';

interface AudioSectionProps {
  content: ParagraphContent | null | undefined;
  paragraphId: number;
  language: string;
  onUpload: (file: File) => void;
  onDelete: () => void;
  isUploading?: boolean;
  isDeleting?: boolean;
}

const AUDIO_ACCEPT = {
  'audio/mpeg': ['.mp3'],
  'audio/ogg': ['.ogg'],
  'audio/wav': ['.wav'],
  'audio/mp4': ['.m4a'],
  'audio/x-m4a': ['.m4a'],
  'audio/aac': ['.m4a'],
};

export function AudioSection({
  content,
  paragraphId,
  language,
  onUpload,
  onDelete,
  isUploading = false,
  isDeleting = false,
}: AudioSectionProps) {
  const hasAudio = !!content?.audio_url;
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.ai-mentor.kz';

  // Build full audio URL
  const audioUrl = content?.audio_url
    ? content.audio_url.startsWith('http')
      ? content.audio_url
      : `${apiUrl}${content.audio_url}`
    : null;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center gap-2">
          <Headphones className="h-5 w-5 text-muted-foreground" />
          <CardTitle className="text-lg">Аудио</CardTitle>
        </div>
        <StatusBadge status={content?.status_audio || 'empty'} />
      </CardHeader>
      <CardContent>
        {hasAudio && audioUrl ? (
          <div className="space-y-4">
            <audio controls className="w-full">
              <source src={audioUrl} type="audio/mpeg" />
              Ваш браузер не поддерживает воспроизведение аудио.
            </audio>
            <div className="flex gap-2">
              <CompactMediaUploader
                accept={AUDIO_ACCEPT}
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
            accept={AUDIO_ACCEPT}
            maxSize={50 * 1024 * 1024}
            onUpload={onUpload}
            isLoading={isUploading}
            label="Загрузить аудио"
            description="MP3, M4A, OGG, WAV. Максимум 50 МБ."
          />
        )}
      </CardContent>
    </Card>
  );
}
