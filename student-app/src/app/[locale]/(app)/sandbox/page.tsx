'use client';

import dynamic from 'next/dynamic';
import { useTranslations } from 'next-intl';
import { Code2, Loader2 } from 'lucide-react';

const PythonSandbox = dynamic(
  () => import('@/components/sandbox/PythonSandbox').then((m) => ({ default: m.PythonSandbox })),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    ),
  }
);

export default function SandboxPage() {
  const t = useTranslations('sandbox');

  return (
    <div className="flex flex-col h-[calc(100vh-5rem)] md:h-[calc(100vh-4rem)] px-4 py-4 md:py-6 mx-auto max-w-5xl w-full">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <Code2 className="h-6 w-6 text-primary" />
        <h1 className="text-xl font-bold text-foreground">{t('title')}</h1>
      </div>

      {/* Sandbox */}
      <div className="flex-1 min-h-0">
        <PythonSandbox />
      </div>
    </div>
  );
}
