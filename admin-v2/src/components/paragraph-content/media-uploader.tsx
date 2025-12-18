'use client';

import { useCallback, useState } from 'react';
import { useDropzone, type FileRejection } from 'react-dropzone';
import { Upload, Loader2, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface MediaUploaderProps {
  accept: Record<string, string[]>;
  maxSize?: number; // in bytes
  onUpload: (file: File) => void;
  isLoading?: boolean;
  label?: string;
  description?: string;
  className?: string;
}

export function MediaUploader({
  accept,
  maxSize = 50 * 1024 * 1024, // 50MB default
  onUpload,
  isLoading = false,
  label = 'Загрузить файл',
  description,
  className,
}: MediaUploaderProps) {
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[], fileRejections: FileRejection[]) => {
      setError(null);

      if (fileRejections.length > 0) {
        const firstError = fileRejections[0]?.errors[0]?.message;
        setError(firstError || 'Файл не принят');
        return;
      }

      if (acceptedFiles.length > 0) {
        onUpload(acceptedFiles[0]);
      }
    },
    [onUpload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    maxSize,
    multiple: false,
    disabled: isLoading,
  });

  return (
    <div className={cn('space-y-2', className)}>
      <div
        {...getRootProps()}
        className={cn(
          'relative border-2 border-dashed rounded-lg p-6 transition-colors cursor-pointer',
          isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25 hover:border-primary/50',
          isLoading && 'cursor-not-allowed opacity-50'
        )}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-2 text-center">
          {isLoading ? (
            <Loader2 className="h-8 w-8 text-primary animate-spin" />
          ) : (
            <Upload className="h-8 w-8 text-muted-foreground" />
          )}
          <div>
            <p className="font-medium">{label}</p>
            {description && (
              <p className="text-sm text-muted-foreground">{description}</p>
            )}
          </div>
        </div>
      </div>
      {error && (
        <div className="flex items-center gap-2 text-sm text-destructive">
          <X className="h-4 w-4" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}

// Compact uploader for replacing existing files
interface CompactMediaUploaderProps {
  accept: Record<string, string[]>;
  maxSize?: number;
  onUpload: (file: File) => void;
  isLoading?: boolean;
  label?: string;
}

export function CompactMediaUploader({
  accept,
  maxSize = 50 * 1024 * 1024,
  onUpload,
  isLoading = false,
  label = 'Заменить',
}: CompactMediaUploaderProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onUpload(acceptedFiles[0]);
      }
    },
    [onUpload]
  );

  const { getRootProps, getInputProps } = useDropzone({
    onDrop,
    accept,
    maxSize,
    multiple: false,
    disabled: isLoading,
  });

  return (
    <div {...getRootProps()}>
      <input {...getInputProps()} />
      <Button variant="outline" size="sm" disabled={isLoading}>
        {isLoading ? (
          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
        ) : (
          <Upload className="h-4 w-4 mr-2" />
        )}
        {label}
      </Button>
    </div>
  );
}
