'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { useQuizSessions } from '@/lib/hooks/use-quiz';
import { Plus, Loader2, Users, Clock, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';

const STATUS_COLORS: Record<string, string> = {
  lobby: 'bg-blue-100 text-blue-700',
  in_progress: 'bg-green-100 text-green-700',
  finished: 'bg-gray-100 text-gray-600',
  cancelled: 'bg-red-100 text-red-600',
};

export default function QuizListPage() {
  const t = useTranslations('quiz');
  const [tab, setTab] = useState<'active' | 'history'>('active');
  const { data: sessions, isLoading } = useQuizSessions();

  const active = (sessions || []).filter(
    (s: Record<string, unknown>) => s.status === 'lobby' || s.status === 'in_progress'
  );
  const history = (sessions || []).filter(
    (s: Record<string, unknown>) => s.status === 'finished' || s.status === 'cancelled'
  );
  const list = tab === 'active' ? active : history;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t('title')}</h1>
        <div className="flex gap-2">
          <Link href="/quiz/quick">
            <Button variant="outline">
              <Zap className="mr-2 h-4 w-4" />
              {t('quickQuestion')}
            </Button>
          </Link>
          <Link href="/quiz/create">
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              {t('createQuiz')}
            </Button>
          </Link>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
        <button
          onClick={() => setTab('active')}
          className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
            tab === 'active' ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground hover:bg-muted/80'
          }`}
        >
          {t('active')} {active.length > 0 && `(${active.length})`}
        </button>
        <button
          onClick={() => setTab('history')}
          className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
            tab === 'history' ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground hover:bg-muted/80'
          }`}
        >
          {t('history')}
        </button>
      </div>

      {/* List */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : list.length === 0 ? (
        <div className="py-12 text-center text-muted-foreground">{t('noQuizzes')}</div>
      ) : (
        <div className="space-y-3">
          {list.map((s: Record<string, unknown>) => (
            <Link key={s.id as number} href={`/quiz/${s.id}`}>
              <div className="flex items-center justify-between rounded-xl border bg-card p-4 transition-colors hover:bg-muted/50">
                <div>
                  <h3 className="font-semibold">{(s.test_title as string) || `Quiz #${s.id}`}</h3>
                  <div className="mt-1 flex items-center gap-3 text-sm text-muted-foreground">
                    {s.class_name ? <span>{String(s.class_name)}</span> : null}
                    <span className="flex items-center gap-1">
                      <Users className="h-3.5 w-3.5" />
                      {s.participant_count as number}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="h-3.5 w-3.5" />
                      {s.question_count as number} {t('questions')}
                    </span>
                  </div>
                </div>
                <span className={`rounded-full px-3 py-1 text-xs font-medium ${STATUS_COLORS[s.status as string] || ''}`}>
                  {t(s.status as string)}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
