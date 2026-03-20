'use client';

import dynamic from 'next/dynamic';
import { useTranslations } from 'next-intl';
import { Code2, Loader2, ListChecks, GraduationCap } from 'lucide-react';
import { useRouter } from 'next/navigation';

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
  const router = useRouter();

  return (
    <div className="flex flex-col h-[calc(100vh-5rem)] md:h-[calc(100vh-4rem)] px-4 py-4 md:py-6 mx-auto max-w-5xl w-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Code2 className="h-6 w-6 text-primary" />
          <h1 className="text-xl font-bold text-foreground">{t('title')}</h1>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => router.push('/sandbox/courses')}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:bg-muted transition-colors"
          >
            <GraduationCap className="h-4 w-4" />
            {t('courses')}
          </button>
          <button
            onClick={() => router.push('/sandbox/challenges')}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            <ListChecks className="h-4 w-4" />
            {t('challenges')}
          </button>
        </div>
      </div>

      {/* Sandbox */}
      <div className="flex-1 min-h-0">
        <PythonSandbox />
      </div>
    </div>
  );
}
