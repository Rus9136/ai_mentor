'use client';

import { useTranslations } from 'next-intl';
import { File, Image, FileText, Download, ExternalLink } from 'lucide-react';
import type { Attachment } from '@/lib/api/homework';

interface AttachmentsListProps {
  attachments: Attachment[];
  title?: string;
  className?: string;
}

const FILE_ICONS: Record<string, React.ReactNode> = {
  image: <Image className="h-5 w-5 text-green-600" />,
  pdf: <FileText className="h-5 w-5 text-red-500" />,
  doc: <File className="h-5 w-5 text-blue-500" />,
  other: <File className="h-5 w-5 text-gray-500" />,
};

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

function getFileUrl(url: string): string {
  // If URL starts with /, prepend API base URL (without /api/v1)
  if (url.startsWith('/')) {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.ai-mentor.kz';
    // Remove /api/v1 or /api/vN suffix to get base URL for static files
    const baseUrl = apiUrl.replace(/\/api\/v\d+$/, '');
    return `${baseUrl}${url}`;
  }
  return url;
}

export function AttachmentsList({ attachments, title, className = '' }: AttachmentsListProps) {
  const t = useTranslations('homework');

  if (!attachments || attachments.length === 0) {
    return null;
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {title && (
        <h3 className="text-sm font-medium text-gray-700 flex items-center gap-2">
          <File className="h-4 w-4" />
          {title}
        </h3>
      )}
      <div className="space-y-2">
        {attachments.map((attachment, index) => (
          <a
            key={`${attachment.url}-${index}`}
            href={getFileUrl(attachment.url)}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-3 p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors group"
          >
            {FILE_ICONS[attachment.type] || FILE_ICONS.other}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate group-hover:text-primary">
                {attachment.name}
              </p>
              <p className="text-xs text-gray-500">
                {formatFileSize(attachment.size)}
              </p>
            </div>
            <ExternalLink className="h-4 w-4 text-gray-400 group-hover:text-primary" />
          </a>
        ))}
      </div>
    </div>
  );
}
