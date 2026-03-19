'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Code2, Loader2, Trophy, Star, Zap } from 'lucide-react';
import { useCodingTopics, useChallenges } from '@/lib/hooks/use-coding';
import { ChallengeCard } from '@/components/sandbox/ChallengeCard';
import type { CodingTopic } from '@/lib/api/coding';
import { useRouter } from 'next/navigation';

export default function ChallengesPage() {
  const t = useTranslations('challenges');
  const router = useRouter();
  const { data: topics, isLoading: topicsLoading } = useCodingTopics();
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);

  // Select first topic by default once loaded
  const activeSlug = selectedSlug ?? topics?.[0]?.slug ?? '';
  const { data: challenges, isLoading: challengesLoading } =
    useChallenges(activeSlug);

  const activeTopic = topics?.find((t: CodingTopic) => t.slug === activeSlug);

  if (topicsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-green-100 dark:bg-green-900/30">
            <Code2 className="h-5 w-5 text-green-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold">{t('title')}</h1>
            <p className="text-sm text-muted-foreground">{t('subtitle')}</p>
          </div>
        </div>
        <button
          onClick={() => router.push('/sandbox')}
          className="px-3 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:bg-muted transition-colors"
        >
          {t('freeCoding')}
        </button>
      </div>

      {/* Topics tabs */}
      <div className="flex gap-2 overflow-x-auto pb-3 mb-4 scrollbar-hide">
        {topics?.map((topic: CodingTopic) => (
          <button
            key={topic.slug}
            onClick={() => setSelectedSlug(topic.slug)}
            className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
              topic.slug === activeSlug
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted/50 text-muted-foreground hover:bg-muted'
            }`}
          >
            {topic.title}
            {topic.solved_challenges > 0 && (
              <span className="text-xs opacity-75">
                {topic.solved_challenges}/{topic.total_challenges}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Topic info */}
      {activeTopic && (
        <div className="flex items-center gap-4 mb-4 px-4 py-3 rounded-lg bg-muted/30 border border-border">
          <div className="flex-1">
            <h2 className="font-semibold">{activeTopic.title}</h2>
            {activeTopic.description && (
              <p className="text-sm text-muted-foreground mt-0.5">
                {activeTopic.description}
              </p>
            )}
          </div>
          <div className="flex items-center gap-3 text-sm">
            {activeTopic.grade_level && (
              <span className="text-muted-foreground">
                {t('grade', { n: activeTopic.grade_level })}
              </span>
            )}
            <div className="flex items-center gap-1">
              <Trophy className="h-4 w-4 text-green-500" />
              <span>
                {activeTopic.solved_challenges}/{activeTopic.total_challenges}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Challenges list */}
      {challengesLoading ? (
        <div className="flex items-center justify-center h-32">
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        </div>
      ) : !challenges?.length ? (
        <div className="text-center py-12 text-muted-foreground">
          {t('noChallenges')}
        </div>
      ) : (
        <div className="space-y-2">
          {challenges.map((ch, i) => (
            <ChallengeCard key={ch.id} challenge={ch} index={i} />
          ))}
        </div>
      )}
    </div>
  );
}
