'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Button } from '@/components/ui/button';
import { Download, Loader2 } from 'lucide-react';
import { downloadReport } from '@/lib/api/quiz';

interface QuizReportDownloadsProps {
  sessionId: number;
}

export default function QuizReportDownloads({ sessionId }: QuizReportDownloadsProps) {
  const t = useTranslations('quiz');
  const [loading, setLoading] = useState<string | null>(null);

  const handleDownload = async (type: 'class' | 'questions') => {
    setLoading(type);
    try {
      const blob = await downloadReport(sessionId, type);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `quiz_${sessionId}_${type}.xlsx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error('Download failed:', e);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="rounded-xl border bg-card p-4">
      <h3 className="mb-3 text-sm font-semibold">{t('reports')}</h3>
      <div className="flex flex-wrap gap-3">
        <Button
          variant="outline"
          size="sm"
          onClick={() => handleDownload('class')}
          disabled={loading !== null}
        >
          {loading === 'class' ? (
            <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
          ) : (
            <Download className="mr-1.5 h-4 w-4" />
          )}
          {t('downloadClassReport')}
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => handleDownload('questions')}
          disabled={loading !== null}
        >
          {loading === 'questions' ? (
            <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
          ) : (
            <Download className="mr-1.5 h-4 w-4" />
          )}
          {t('downloadQuestionReport')}
        </Button>
      </div>
    </div>
  );
}
