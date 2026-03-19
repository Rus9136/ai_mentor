'use client';

import { useState, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { useTranslations } from 'next-intl';
import { Play, Send, Loader2 } from 'lucide-react';
import { CodeOutput } from '@/components/sandbox/CodeOutput';
import { runPython, ensurePyodideLoaded, isPyodideReady, type PythonResult } from '@/lib/pyodide/pyodide-runner';
import type { StudentQuestionResponse, SubmissionResult } from '@/lib/api/homework';

const CodeEditor = dynamic(
  () => import('@/components/sandbox/CodeEditor').then((m) => ({ default: m.CodeEditor })),
  {
    ssr: false,
    loading: () => (
      <div className="h-48 border border-border rounded-lg bg-muted/30 flex items-center justify-center">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    ),
  }
);

interface CodeQuestionProps {
  question: StudentQuestionResponse;
  questionNumber: number;
  onAnswer: (answerCode: string) => Promise<SubmissionResult>;
}

export function CodeQuestion({ question, questionNumber, onAnswer }: CodeQuestionProps) {
  const t = useTranslations('homework');
  const tSandbox = useTranslations('sandbox');

  const [code, setCode] = useState('# \n');
  const [stdin, setStdin] = useState('');
  const [testResult, setTestResult] = useState<PythonResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [pyodideLoading, setPyodideLoading] = useState(!isPyodideReady());

  // Preload Pyodide
  useState(() => {
    if (!isPyodideReady()) {
      ensurePyodideLoaded((msg) => {
        if (msg === 'ready') setPyodideLoading(false);
      }).catch(() => setPyodideLoading(false));
    }
  });

  const handleTest = useCallback(async () => {
    if (isRunning) return;
    setIsRunning(true);
    setTestResult(null);
    try {
      const result = await runPython(code, stdin);
      setTestResult(result);
    } catch {
      setTestResult({
        stdout: '',
        stderr: '',
        error: 'Failed to execute',
        executionTimeMs: 0,
      });
    } finally {
      setIsRunning(false);
    }
  }, [code, stdin, isRunning]);

  const handleSubmit = useCallback(async () => {
    if (isSubmitting || !code.trim()) return;
    setIsSubmitting(true);
    try {
      await onAnswer(code);
      setSubmitted(true);
    } catch (error) {
      console.error('Failed to submit code:', error);
    } finally {
      setIsSubmitting(false);
    }
  }, [code, isSubmitting, onAnswer]);

  if (submitted) {
    return (
      <div className="text-center py-4">
        <p className="text-sm text-muted-foreground">{t('question.needsReview')}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Question Text */}
      <div>
        <p className="text-sm text-primary font-medium mb-2">
          {t('question.number', { current: questionNumber, total: questionNumber })}
        </p>
        <p className="font-semibold text-gray-900">{question.question_text}</p>
      </div>

      {/* Code Editor */}
      <div style={{ minHeight: '200px' }}>
        <CodeEditor
          value={code}
          onChange={setCode}
          onRun={handleTest}
          height="200px"
        />
      </div>

      {/* Stdin */}
      <div>
        <label className="text-xs font-medium text-muted-foreground">
          {tSandbox('testInput')}
        </label>
        <textarea
          value={stdin}
          onChange={(e) => setStdin(e.target.value)}
          rows={2}
          className="w-full mt-1 resize-y rounded-md border border-border bg-background px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary/30"
          placeholder="5&#10;Hello"
        />
      </div>

      {/* Test Output */}
      {(testResult || isRunning) && (
        <div className="border border-border rounded-lg bg-muted/20">
          <div className="px-3 py-1.5 border-b border-border/50 text-xs font-semibold text-muted-foreground uppercase">
            {tSandbox('output')}
          </div>
          <CodeOutput result={testResult} isRunning={isRunning} />
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleTest}
          disabled={isRunning || pyodideLoading}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors disabled:opacity-50"
        >
          {isRunning ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          {tSandbox('run')}
        </button>

        <button
          onClick={handleSubmit}
          disabled={isSubmitting || !code.trim()}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-primary text-white text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          {isSubmitting ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
          {t('question.submit')}
        </button>
      </div>
    </div>
  );
}
