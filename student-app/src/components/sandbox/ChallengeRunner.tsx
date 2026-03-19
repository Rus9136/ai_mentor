'use client';

import { useState, useCallback, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { useTranslations } from 'next-intl';
import {
  Play,
  CheckCircle2,
  Loader2,
  ChevronDown,
  ChevronUp,
  Lightbulb,
  Trophy,
  Sparkles,
} from 'lucide-react';
import { CodeOutput } from './CodeOutput';
import { TestResults } from './TestResults';
import {
  ensurePyodideLoaded,
  runPython,
  isPyodideReady,
  type PythonResult,
} from '@/lib/pyodide/pyodide-runner';
import {
  runChallengeTests,
  type ChallengeRunResult,
  type TestCaseInput,
} from '@/lib/pyodide/challenge-runner';
import { useSubmitSolution } from '@/lib/hooks/use-coding';
import type { ChallengeDetail } from '@/lib/api/coding';

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

interface ChallengeRunnerProps {
  challenge: ChallengeDetail;
}

export function ChallengeRunner({ challenge }: ChallengeRunnerProps) {
  const t = useTranslations('challenges');
  const tSandbox = useTranslations('sandbox');

  const [code, setCode] = useState(
    challenge.best_submission?.code ?? challenge.starter_code ?? ''
  );
  const [stdinOpen, setStdinOpen] = useState(false);
  const [stdin, setStdin] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  const [runResult, setRunResult] = useState<PythonResult | null>(null);
  const [testResult, setTestResult] = useState<ChallengeRunResult | null>(null);
  const [showHints, setShowHints] = useState<number>(0);
  const [justSolved, setJustSolved] = useState(false);

  const [pyodideStatus, setPyodideStatus] = useState<
    'idle' | 'loading' | 'ready' | 'error'
  >(isPyodideReady() ? 'ready' : 'idle');

  const submitMutation = useSubmitSolution(challenge.id);

  // Preload Pyodide
  useEffect(() => {
    if (isPyodideReady()) {
      setPyodideStatus('ready');
      return;
    }
    setPyodideStatus('loading');
    ensurePyodideLoaded((msg) => {
      if (msg === 'ready') setPyodideStatus('ready');
    }).catch(() => setPyodideStatus('error'));
  }, []);

  // Run (free execution with optional stdin)
  const handleRun = useCallback(async () => {
    if (isRunning || isChecking) return;
    setIsRunning(true);
    setRunResult(null);
    setTestResult(null);

    try {
      if (!isPyodideReady()) {
        await ensurePyodideLoaded();
      }
      const res = await runPython(code, stdin);
      setRunResult(res);
    } catch {
      setRunResult({
        stdout: '',
        stderr: '',
        error: 'Failed to execute',
        executionTimeMs: 0,
      });
    } finally {
      setIsRunning(false);
    }
  }, [code, stdin, isRunning, isChecking]);

  // Check (run all test cases)
  const handleCheck = useCallback(async () => {
    if (isRunning || isChecking) return;
    setIsChecking(true);
    setRunResult(null);
    setTestResult(null);

    try {
      if (!isPyodideReady()) {
        await ensurePyodideLoaded();
      }
      const result = await runChallengeTests(
        code,
        challenge.test_cases as TestCaseInput[],
        challenge.time_limit_ms ?? 5000
      );
      setTestResult(result);

      // Auto-submit if all passed
      if (result.allPassed) {
        submitMutation.mutate(
          {
            code,
            tests_passed: result.passed,
            tests_total: result.total,
            execution_time_ms: result.totalTimeMs,
          },
          {
            onSuccess: (sub) => {
              if (sub.xp_earned > 0) {
                setJustSolved(true);
              }
            },
          }
        );
      } else {
        // Submit failed attempt too
        submitMutation.mutate({
          code,
          tests_passed: result.passed,
          tests_total: result.total,
          execution_time_ms: result.totalTimeMs,
        });
      }
    } catch {
      setTestResult(null);
    } finally {
      setIsChecking(false);
    }
  }, [code, challenge, isRunning, isChecking, submitMutation]);

  const isLoading = pyodideStatus === 'loading';
  const hints = challenge.hints ?? [];

  return (
    <div className="flex flex-col h-full gap-3">
      {/* Solved celebration */}
      {justSolved && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-green-100 dark:bg-green-900/30 border border-green-300 dark:border-green-800">
          <Trophy className="h-5 w-5 text-yellow-500" />
          <div>
            <p className="font-semibold text-green-800 dark:text-green-300">
              {t('solved')}
            </p>
            <p className="text-sm text-green-700 dark:text-green-400">
              +{challenge.points} XP
            </p>
          </div>
          <Sparkles className="h-5 w-5 text-yellow-400 ml-auto" />
        </div>
      )}

      {/* Toolbar */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          {/* Run */}
          <button
            onClick={handleRun}
            disabled={isRunning || isChecking || isLoading}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-gray-200 dark:bg-gray-700 text-sm font-medium hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 transition-colors"
          >
            {isRunning ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            {tSandbox('run')}
          </button>

          {/* Check */}
          <button
            onClick={handleCheck}
            disabled={isRunning || isChecking || isLoading}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-green-600 text-white text-sm font-semibold hover:bg-green-700 disabled:opacity-50 transition-colors"
          >
            {isChecking ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <CheckCircle2 className="h-4 w-4" />
            )}
            {t('check')}
          </button>
        </div>

        <div className="flex items-center gap-2">
          {isLoading && (
            <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Loader2 className="h-3 w-3 animate-spin" />
              {tSandbox('loading')}
            </span>
          )}
          {pyodideStatus === 'ready' && (
            <span className="text-xs text-muted-foreground hidden md:block">
              Ctrl+Enter
            </span>
          )}
        </div>
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

      {/* Stdin */}
      <div className="border border-border rounded-lg overflow-hidden">
        <button
          onClick={() => setStdinOpen(!stdinOpen)}
          className="flex items-center justify-between w-full px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-muted/50 transition-colors"
        >
          <span>{tSandbox('testInput')}</span>
          {stdinOpen ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </button>
        {stdinOpen && (
          <div className="px-3 pb-3">
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

      {/* Hints */}
      {hints.length > 0 && (
        <div>
          <button
            onClick={() => setShowHints(Math.min(showHints + 1, hints.length))}
            disabled={showHints >= hints.length}
            className="flex items-center gap-1.5 text-sm text-amber-600 hover:text-amber-700 disabled:opacity-40 transition-colors"
          >
            <Lightbulb className="h-4 w-4" />
            {showHints === 0
              ? t('showHint')
              : t('showNextHint', { n: showHints, total: hints.length })}
          </button>
          {showHints > 0 && (
            <div className="mt-2 space-y-1.5">
              {hints.slice(0, showHints).map((hint: string, i: number) => (
                <div
                  key={i}
                  className="px-3 py-2 rounded-md bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 text-sm"
                >
                  <span className="font-medium text-amber-700 dark:text-amber-400">
                    {t('hint')} {i + 1}:
                  </span>{' '}
                  {hint}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Test Results */}
      {testResult && (
        <TestResults
          results={testResult.testResults}
          passed={testResult.passed}
          total={testResult.total}
        />
      )}

      {/* Free run output */}
      {runResult && !testResult && (
        <div className="border border-border rounded-lg bg-muted/20 min-h-[80px] max-h-[200px] overflow-y-auto">
          <div className="px-3 py-2 border-b border-border/50 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
            {tSandbox('output')}
          </div>
          <CodeOutput result={runResult} isRunning={false} />
        </div>
      )}
    </div>
  );
}
