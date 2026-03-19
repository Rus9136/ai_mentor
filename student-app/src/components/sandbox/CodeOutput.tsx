'use client';

import { useTranslations } from 'next-intl';
import { Loader2 } from 'lucide-react';
import type { PythonResult } from '@/lib/pyodide/pyodide-runner';

interface CodeOutputProps {
  result: PythonResult | null;
  isRunning: boolean;
}

export function CodeOutput({ result, isRunning }: CodeOutputProps) {
  const t = useTranslations('sandbox');

  if (isRunning) {
    return (
      <div className="flex items-center gap-2 p-4 text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span className="text-sm">{t('running')}</span>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="p-4 text-sm text-muted-foreground">
        {t('emptyOutput')}
      </div>
    );
  }

  return (
    <div className="p-3 space-y-2 font-mono text-sm">
      {/* stdout */}
      {result.stdout && (
        <pre className="whitespace-pre-wrap text-green-700 dark:text-green-400">
          {result.stdout}
        </pre>
      )}

      {/* stderr */}
      {result.stderr && (
        <pre className="whitespace-pre-wrap text-yellow-600 dark:text-yellow-400">
          {result.stderr}
        </pre>
      )}

      {/* error */}
      {result.error && (
        <pre className="whitespace-pre-wrap text-red-600 dark:text-red-400">
          {result.error}
        </pre>
      )}

      {/* no output at all */}
      {!result.stdout && !result.stderr && !result.error && (
        <span className="text-muted-foreground">{t('emptyOutput')}</span>
      )}

      {/* execution time */}
      <div className="text-xs text-muted-foreground pt-1 border-t border-border/50">
        {t('executionTime', { ms: result.executionTimeMs })}
      </div>
    </div>
  );
}
