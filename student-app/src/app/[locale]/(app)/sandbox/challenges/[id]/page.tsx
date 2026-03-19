'use client';

import { useParams, useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import dynamic from 'next/dynamic';
import {
  ArrowLeft,
  Loader2,
  Star,
  CheckCircle2,
} from 'lucide-react';
import { useChallengeDetail } from '@/lib/hooks/use-coding';

const ChallengeRunner = dynamic(
  () =>
    import('@/components/sandbox/ChallengeRunner').then((m) => ({
      default: m.ChallengeRunner,
    })),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    ),
  }
);

const difficultyLabels: Record<string, string> = {
  easy: 'Easy',
  medium: 'Medium',
  hard: 'Hard',
};

const difficultyColors: Record<string, string> = {
  easy: 'text-green-600 bg-green-100 dark:bg-green-900/30',
  medium: 'text-amber-600 bg-amber-100 dark:bg-amber-900/30',
  hard: 'text-red-600 bg-red-100 dark:bg-red-900/30',
};

export default function ChallengePage() {
  const params = useParams();
  const router = useRouter();
  const t = useTranslations('challenges');

  const challengeId = Number(params.id);
  const { data: challenge, isLoading } = useChallengeDetail(
    isNaN(challengeId) ? undefined : challengeId
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!challenge) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        {t('notFound')}
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-5rem)] md:h-[calc(100vh-4rem)]">
      {/* Header bar */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
        <button
          onClick={() => router.push('/sandbox/challenges')}
          className="p-1.5 rounded-md hover:bg-muted transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
        </button>

        <div className="flex-1 min-w-0">
          <h1 className="text-sm font-semibold truncate">{challenge.title}</h1>
        </div>

        {challenge.status === 'solved' && (
          <CheckCircle2 className="h-5 w-5 text-green-500" />
        )}

        <span
          className={`px-2 py-0.5 rounded text-xs font-medium ${
            difficultyColors[challenge.difficulty]
          }`}
        >
          {t(challenge.difficulty)}
        </span>

        <span className="flex items-center gap-1 text-xs text-amber-500 font-medium">
          <Star className="h-3.5 w-3.5" />
          {challenge.points} XP
        </span>
      </div>

      {/* Main content: description + editor split on desktop */}
      <div className="flex-1 min-h-0 flex flex-col md:flex-row">
        {/* Left panel: description */}
        <div className="md:w-[380px] md:min-w-[320px] md:max-w-[450px] border-b md:border-b-0 md:border-r border-border overflow-y-auto">
          <div className="p-4">
            <h2 className="font-semibold mb-2">{t('description')}</h2>
            <div className="text-sm text-foreground/80 whitespace-pre-wrap leading-relaxed">
              {challenge.description}
            </div>

            {/* Visible test cases as examples */}
            {challenge.test_cases.filter((tc) => !tc.is_hidden).length > 0 && (
              <div className="mt-4">
                <h3 className="text-sm font-semibold mb-2">{t('examples')}</h3>
                <div className="space-y-3">
                  {challenge.test_cases
                    .filter((tc) => !tc.is_hidden)
                    .map((tc, i) => (
                      <div
                        key={i}
                        className="rounded-md border border-border bg-muted/30 overflow-hidden"
                      >
                        {tc.input && (
                          <div className="px-3 py-2 border-b border-border/50">
                            <span className="text-xs font-semibold text-muted-foreground">
                              {t('input')}:
                            </span>
                            <pre className="text-sm font-mono mt-0.5">
                              {tc.input}
                            </pre>
                          </div>
                        )}
                        <div className="px-3 py-2">
                          <span className="text-xs font-semibold text-muted-foreground">
                            {t('output')}:
                          </span>
                          <pre className="text-sm font-mono mt-0.5">
                            {tc.expected_output}
                          </pre>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right panel: code editor + test results */}
        <div className="flex-1 min-h-0 min-w-0 p-3 overflow-y-auto">
          <ChallengeRunner challenge={challenge} />
        </div>
      </div>
    </div>
  );
}
