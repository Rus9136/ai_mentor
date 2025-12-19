'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, FileText, BookOpen, Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { RoleGuard } from '@/components/auth';
import {
  LanguageSwitcher,
  ExplainSection,
  AudioSection,
  SlidesSection,
  VideoSection,
  CardsSection,
} from '@/components/paragraph-content';
import { useTextbook, useParagraph } from '@/lib/hooks/use-textbooks';
import {
  useParagraphContent,
  useUpdateParagraphContent,
  useUpdateParagraphCards,
  useUploadAudio,
  useUploadSlides,
  useUploadVideo,
  useDeleteAudio,
  useDeleteSlides,
  useDeleteVideo,
} from '@/lib/hooks/use-paragraph-content';
import type { CardItem } from '@/types';

export default function ParagraphContentPage() {
  const params = useParams();
  const router = useRouter();
  const textbookId = Number(params.id);
  const paragraphId = Number(params.paragraphId);

  const [language, setLanguage] = useState<'ru' | 'kz'>('ru');

  // Data fetching
  const { data: textbook, isLoading: textbookLoading } = useTextbook(textbookId, false);
  const { data: paragraph, isLoading: paragraphLoading } = useParagraph(paragraphId, false);
  const { data: content, isLoading: contentLoading } = useParagraphContent(
    paragraphId,
    language,
    false
  );

  // Mutations
  const updateContent = useUpdateParagraphContent(false);
  const updateCards = useUpdateParagraphCards(false);
  const uploadAudio = useUploadAudio(false);
  const uploadSlides = useUploadSlides(false);
  const uploadVideo = useUploadVideo(false);
  const deleteAudio = useDeleteAudio(false);
  const deleteSlides = useDeleteSlides(false);
  const deleteVideo = useDeleteVideo(false);

  // Handlers
  const handleSaveExplain = (explainText: string) => {
    updateContent.mutate({
      paragraphId,
      language,
      data: { explain_text: explainText },
    });
  };

  const handleSaveCards = (cards: CardItem[]) => {
    updateCards.mutate({
      paragraphId,
      language,
      cards,
    });
  };

  const handleUploadAudio = (file: File) => {
    uploadAudio.mutate({ paragraphId, language, file });
  };

  const handleUploadSlides = (file: File) => {
    uploadSlides.mutate({ paragraphId, language, file });
  };

  const handleUploadVideo = (file: File) => {
    uploadVideo.mutate({ paragraphId, language, file });
  };

  const handleDeleteAudio = () => {
    deleteAudio.mutate({ paragraphId, language });
  };

  const handleDeleteSlides = () => {
    deleteSlides.mutate({ paragraphId, language });
  };

  const handleDeleteVideo = () => {
    deleteVideo.mutate({ paragraphId, language });
  };

  // Loading state
  if (textbookLoading || paragraphLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10" />
          <div className="space-y-2">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-4 w-48" />
          </div>
        </div>
        <div className="grid gap-6">
          <Skeleton className="h-64 w-full" />
          <Skeleton className="h-48 w-full" />
          <Skeleton className="h-48 w-full" />
        </div>
      </div>
    );
  }

  // Not found state
  if (!textbook || !paragraph) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <p className="text-muted-foreground">Параграф не найден</p>
        <Button variant="link" onClick={() => router.back()}>
          Вернуться назад
        </Button>
      </div>
    );
  }

  return (
    <RoleGuard allowedRoles={['super_admin']}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => router.back()}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold tracking-tight">
                  Контент параграфа
                </h1>
              </div>
              <div className="flex items-center gap-2 text-muted-foreground mt-1">
                <BookOpen className="h-4 w-4" />
                <span className="text-sm">{textbook.title}</span>
                <span className="text-muted-foreground">›</span>
                <FileText className="h-4 w-4" />
                <span className="text-sm">§{paragraph.number}. {paragraph.title}</span>
                <Badge variant="secondary" className="ml-2">
                  {textbook.grade_level} класс
                </Badge>
              </div>
            </div>
          </div>

          <LanguageSwitcher value={language} onChange={setLanguage} />
        </div>

        {/* Content loading indicator */}
        {contentLoading && (
          <Alert>
            <Loader2 className="h-4 w-4 animate-spin" />
            <AlertDescription>Загрузка контента...</AlertDescription>
          </Alert>
        )}

        {/* Content sections */}
        <div className="grid gap-6">
          <ExplainSection
            content={content}
            paragraphId={paragraphId}
            language={language}
            onSave={handleSaveExplain}
            isLoading={updateContent.isPending}
          />

          <div className="grid gap-6 lg:grid-cols-2">
            <AudioSection
              content={content}
              paragraphId={paragraphId}
              language={language}
              onUpload={handleUploadAudio}
              onDelete={handleDeleteAudio}
              isUploading={uploadAudio.isPending}
              isDeleting={deleteAudio.isPending}
            />

            <SlidesSection
              content={content}
              paragraphId={paragraphId}
              language={language}
              onUpload={handleUploadSlides}
              onDelete={handleDeleteSlides}
              isUploading={uploadSlides.isPending}
              isDeleting={deleteSlides.isPending}
            />
          </div>

          <VideoSection
            content={content}
            paragraphId={paragraphId}
            language={language}
            onUpload={handleUploadVideo}
            onDelete={handleDeleteVideo}
            isUploading={uploadVideo.isPending}
            isDeleting={deleteVideo.isPending}
          />

          <CardsSection
            content={content}
            paragraphId={paragraphId}
            language={language}
            onSave={handleSaveCards}
            isLoading={updateCards.isPending}
          />
        </div>
      </div>
    </RoleGuard>
  );
}
