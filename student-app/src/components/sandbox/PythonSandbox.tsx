'use client';

import { useState, useCallback, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { useTranslations } from 'next-intl';
import { Play, Square, Trash2, ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import { CodeOutput } from './CodeOutput';
import {
  ensurePyodideLoaded,
  runPython,
  isPyodideReady,
  type PythonResult,
} from '@/lib/pyodide/pyodide-runner';

// Dynamic import for CodeMirror (browser-only)
const CodeEditor = dynamic(
  () => import('./CodeEditor').then((m) => ({ default: m.CodeEditor })),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-64 border border-border rounded-lg bg-muted/30">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    ),
  }
);

interface PythonSandboxProps {
  initialCode?: string;
  showStdin?: boolean;
}

export function PythonSandbox({ initialCode, showStdin = true }: PythonSandboxProps) {
  const t = useTranslations('sandbox');
  const starterCode = initialCode ?? t('starterCode');

  const [code, setCode] = useState(starterCode);
  const [stdin, setStdin] = useState('');
  const [stdinOpen, setStdinOpen] = useState(false);
  const [result, setResult] = useState<PythonResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [pyodideStatus, setPyodideStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>(
    isPyodideReady() ? 'ready' : 'idle'
  );

  // Preload Pyodide on mount
  useEffect(() => {
    if (isPyodideReady()) {
      setPyodideStatus('ready');
      return;
    }
    setPyodideStatus('loading');
    ensurePyodideLoaded((msg) => {
      if (msg === 'ready') setPyodideStatus('ready');
    }).catch(() => {
      setPyodideStatus('error');
    });
  }, []);

  const handleRun = useCallback(async () => {
    if (isRunning) return;

    setIsRunning(true);
    setResult(null);

    try {
      if (!isPyodideReady()) {
        setPyodideStatus('loading');
        await ensurePyodideLoaded((msg) => {
          if (msg === 'ready') setPyodideStatus('ready');
        });
      }
      const res = await runPython(code, stdin);
      setResult(res);
    } catch {
      setResult({
        stdout: '',
        stderr: '',
        error: 'Failed to execute Python code',
        executionTimeMs: 0,
      });
    } finally {
      setIsRunning(false);
    }
  }, [code, stdin, isRunning]);

  const handleClear = useCallback(() => {
    setResult(null);
  }, []);

  const isLoading = pyodideStatus === 'loading';

  return (
    <div className="flex flex-col h-full gap-3">
      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {/* Run button */}
          <button
            onClick={handleRun}
            disabled={isRunning || isLoading}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-green-600 text-white text-sm font-semibold hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isRunning ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            {isRunning ? t('running') : t('run')}
          </button>

          {/* Clear output */}
          {result && (
            <button
              onClick={handleClear}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:bg-muted transition-colors"
            >
              <Trash2 className="h-3.5 w-3.5" />
              {t('clear')}
            </button>
          )}
        </div>

        {/* Pyodide status */}
        {isLoading && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Loader2 className="h-3 w-3 animate-spin" />
            {t('loading')}
          </div>
        )}

        {/* Ctrl+Enter hint */}
        {pyodideStatus === 'ready' && !isRunning && (
          <span className="text-xs text-muted-foreground hidden md:block">
            Ctrl+Enter
          </span>
        )}
      </div>

      {/* Code Editor */}
      <div className="flex-1 min-h-0" style={{ minHeight: '200px' }}>
        <CodeEditor
          value={code}
          onChange={setCode}
          onRun={handleRun}
          height="100%"
        />
      </div>

      {/* Stdin (collapsible) */}
      {showStdin && (
        <div className="border border-border rounded-lg overflow-hidden">
          <button
            onClick={() => setStdinOpen(!stdinOpen)}
            className="flex items-center justify-between w-full px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-muted/50 transition-colors"
          >
            <span>{t('testInput')}</span>
            {stdinOpen ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </button>
          {stdinOpen && (
            <div className="px-3 pb-3">
              <p className="text-xs text-muted-foreground mb-1.5">{t('testInputHint')}</p>
              <textarea
                value={stdin}
                onChange={(e) => setStdin(e.target.value)}
                rows={3}
                className="w-full resize-y rounded-md border border-border bg-background px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary/30"
                placeholder="5&#10;Hello"
              />
            </div>
          )}
        </div>
      )}

      {/* Output Panel */}
      <div className="border border-border rounded-lg bg-muted/20 min-h-[100px] max-h-[300px] overflow-y-auto">
        <div className="px-3 py-2 border-b border-border/50 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
          {t('output')}
        </div>
        <CodeOutput result={result} isRunning={isRunning} />
      </div>
    </div>
  );
}
