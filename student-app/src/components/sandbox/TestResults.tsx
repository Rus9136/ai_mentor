'use client';

import { useTranslations } from 'next-intl';
import { CheckCircle2, XCircle, Lock, AlertCircle } from 'lucide-react';
import type { TestCaseResult } from '@/lib/pyodide/challenge-runner';

interface TestResultsProps {
  results: TestCaseResult[];
  passed: number;
  total: number;
}

export function TestResults({ results, passed, total }: TestResultsProps) {
  const t = useTranslations('challenges');
  const allPassed = passed === total;

  return (
    <div className="space-y-2">
      {/* Summary */}
      <div
        className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold ${
          allPassed
            ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
            : 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400'
        }`}
      >
        {allPassed ? (
          <CheckCircle2 className="h-4 w-4" />
        ) : (
          <AlertCircle className="h-4 w-4" />
        )}
        {t('testsPassed', { passed, total })}
      </div>

      {/* Individual tests */}
      <div className="space-y-1.5">
        {results.map((r) => (
          <div
            key={r.index}
            className={`px-3 py-2 rounded-md border text-sm ${
              r.passed
                ? 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/10'
                : 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/10'
            }`}
          >
            <div className="flex items-center gap-2">
              {r.is_hidden ? (
                <Lock className="h-3.5 w-3.5 text-muted-foreground" />
              ) : r.passed ? (
                <CheckCircle2 className="h-3.5 w-3.5 text-green-600" />
              ) : (
                <XCircle className="h-3.5 w-3.5 text-red-600" />
              )}
              <span className="font-medium">
                {t('testN', { n: r.index + 1 })}
                {r.description && !r.is_hidden && (
                  <span className="font-normal text-muted-foreground ml-1">
                    — {r.description}
                  </span>
                )}
              </span>
            </div>

            {/* Show details for non-hidden tests */}
            {!r.is_hidden && !r.passed && (
              <div className="mt-1.5 pl-6 text-xs font-mono space-y-0.5">
                {r.input && (
                  <div>
                    <span className="text-muted-foreground">{t('input')}: </span>
                    <span>{r.input}</span>
                  </div>
                )}
                <div>
                  <span className="text-muted-foreground">{t('expected')}: </span>
                  <span className="text-green-700 dark:text-green-400">
                    {r.expected}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground">{t('actual')}: </span>
                  <span className="text-red-700 dark:text-red-400">
                    {r.actual || '(empty)'}
                  </span>
                </div>
                {r.error && (
                  <div className="text-red-600 dark:text-red-400">
                    {r.error.split('\n').slice(-1)[0]}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
