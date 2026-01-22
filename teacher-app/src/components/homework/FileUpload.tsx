'use client';

import { useState, useRef } from 'react';
import { useTranslations } from 'next-intl';
import { Upload, X, File, Image, FileText, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { uploadHomeworkFile } from '@/lib/api/homework';
import type { Attachment } from '@/types/homework';

interface FileUploadProps {
  attachments: Attachment[];
  onAttachmentsChange: (attachments: Attachment[]) => void;
  maxFiles?: number;
  disabled?: boolean;
}

const FILE_ICONS: Record<string, React.ReactNode> = {
  image: <Image className="h-4 w-4" />,
  pdf: <FileText className="h-4 w-4 text-red-500" />,
  doc: <File className="h-4 w-4 text-blue-500" />,
  other: <File className="h-4 w-4" />,
};

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export function FileUpload({
  attachments,
  onAttachmentsChange,
  maxFiles = 10,
  disabled = false,
}: FileUploadProps) {
  const t = useTranslations('homework');
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    // Check max files limit
    if (attachments.length + files.length > maxFiles) {
      setError(t('errors.maxFilesExceeded', { max: maxFiles }));
      return;
    }

    setIsUploading(true);
    setError(null);

    const newAttachments: Attachment[] = [];

    for (const file of Array.from(files)) {
      try {
        const result = await uploadHomeworkFile(file);
        newAttachments.push(result);
      } catch (err: any) {
        const errorMessage = err?.response?.data?.detail || err?.message || t('errors.uploadFailed');
        setError(errorMessage);
        break;
      }
    }

    if (newAttachments.length > 0) {
      onAttachmentsChange([...attachments, ...newAttachments]);
    }

    setIsUploading(false);

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleRemove = (index: number) => {
    const updated = attachments.filter((_, i) => i !== index);
    onAttachmentsChange(updated);
  };

  const handleDrop = async (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();

    if (disabled || isUploading) return;

    const files = event.dataTransfer.files;
    if (!files || files.length === 0) return;

    // Create a fake event to reuse handleFileSelect logic
    const fakeEvent = {
      target: { files },
    } as React.ChangeEvent<HTMLInputElement>;

    await handleFileSelect(fakeEvent);
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
  };

  return (
    <div className="space-y-3">
      {/* Drop zone */}
      <div
        className={`
          border-2 border-dashed rounded-lg p-4 text-center transition-colors
          ${disabled ? 'bg-muted cursor-not-allowed' : 'hover:border-primary cursor-pointer'}
          ${isUploading ? 'border-primary bg-primary/5' : 'border-muted-foreground/25'}
        `}
        onClick={() => !disabled && !isUploading && fileInputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt"
          className="hidden"
          onChange={handleFileSelect}
          disabled={disabled || isUploading}
        />

        {isUploading ? (
          <div className="flex flex-col items-center gap-2 py-2">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">{t('file.uploading')}</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2 py-2">
            <Upload className="h-6 w-6 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium">{t('file.dropOrClick')}</p>
              <p className="text-xs text-muted-foreground">
                {t('file.supportedFormats')}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Error message */}
      {error && (
        <p className="text-sm text-destructive">{error}</p>
      )}

      {/* Uploaded files list */}
      {attachments.length > 0 && (
        <div className="space-y-2">
          {attachments.map((attachment, index) => (
            <div
              key={`${attachment.url}-${index}`}
              className="flex items-center gap-3 p-2 bg-muted/50 rounded-md"
            >
              {FILE_ICONS[attachment.type] || FILE_ICONS.other}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{attachment.name}</p>
                <p className="text-xs text-muted-foreground">
                  {formatFileSize(attachment.size)}
                </p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => handleRemove(index)}
                disabled={disabled}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      )}

      {/* Files count */}
      {attachments.length > 0 && (
        <p className="text-xs text-muted-foreground">
          {t('file.count', { count: attachments.length, max: maxFiles })}
        </p>
      )}
    </div>
  );
}
