'use client';

import { FileText, Download, Loader2, CheckCircle, XCircle, Clock } from 'lucide-react';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MediaUploader } from '@/components/paragraph-content/media-uploader';
import { useConversionStatus, useUploadPdf } from '@/lib/hooks/use-textbook-conversions';
import { textbookConversionsApi } from '@/lib/api/textbook-conversions';
import type { ConversionStatus } from '@/types';

const statusConfig: Record<ConversionStatus, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: typeof Clock }> = {
  PENDING: { label: 'Ожидание', variant: 'secondary', icon: Clock },
  PROCESSING: { label: 'Обработка...', variant: 'outline', icon: Loader2 },
  COMPLETED: { label: 'Готово', variant: 'default', icon: CheckCircle },
  FAILED: { label: 'Ошибка', variant: 'destructive', icon: XCircle },
};

interface ConversionSectionProps {
  textbookId: number;
}

export function ConversionSection({ textbookId }: ConversionSectionProps) {
  const { data: conversion, isLoading: statusLoading } = useConversionStatus(textbookId);
  const uploadMutation = useUploadPdf(textbookId);

  const isActive = conversion?.status === 'PENDING' || conversion?.status === 'PROCESSING';
  const isCompleted = conversion?.status === 'COMPLETED';

  const handleUpload = (file: File) => {
    uploadMutation.mutate(file);
  };

  const handleDownload = async () => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (!token) return;

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'https://api.ai-mentor.kz/api/v1'}/admin/global/textbooks/${textbookId}/conversions/mmd`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!response.ok) throw new Error('Download failed');
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `textbook_${textbookId}.mmd`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // handled silently
    }
  };

  const config = conversion ? statusConfig[conversion.status] : null;

  return (
    <Card className="md:col-span-2">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          PDF → Mathpix Markdown
        </CardTitle>
        <CardDescription>
          Загрузите PDF учебника для автоматической конвертации в Mathpix Markdown (MMD)
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Status */}
        {conversion && config && (
          <div className="flex items-center justify-between rounded-lg border p-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Badge variant={config.variant}>
                  {(conversion.status === 'PROCESSING') ? (
                    <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                  ) : (
                    <config.icon className="mr-1 h-3 w-3" />
                  )}
                  {config.label}
                </Badge>
                <span className="text-sm text-muted-foreground">
                  Конверсия #{conversion.id}
                </span>
              </div>
              {conversion.started_at && (
                <p className="text-xs text-muted-foreground">
                  Начата: {format(new Date(conversion.started_at), 'dd MMM yyyy, HH:mm', { locale: ru })}
                </p>
              )}
              {conversion.completed_at && (
                <p className="text-xs text-muted-foreground">
                  Завершена: {format(new Date(conversion.completed_at), 'dd MMM yyyy, HH:mm', { locale: ru })}
                </p>
              )}
              {conversion.error_message && (
                <p className="text-sm text-destructive">{conversion.error_message}</p>
              )}
            </div>

            {isCompleted && (
              <Button variant="outline" size="sm" onClick={handleDownload}>
                <Download className="mr-2 h-4 w-4" />
                Скачать MMD
              </Button>
            )}
          </div>
        )}

        {/* Upload */}
        {!isActive && (
          <MediaUploader
            accept={{ 'application/pdf': ['.pdf'] }}
            maxSize={100 * 1024 * 1024}
            onUpload={handleUpload}
            isLoading={uploadMutation.isPending}
            label="Загрузить PDF учебника"
            description="PDF до 100 МБ. Конвертация занимает 1-10 минут в зависимости от размера."
          />
        )}

        {isActive && (
          <div className="flex items-center gap-3 rounded-lg bg-muted p-4">
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
            <p className="text-sm">Конвертация в процессе, статус обновляется автоматически...</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
