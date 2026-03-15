'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { useRouter } from '@/i18n/routing';
import { Button } from '@/components/ui/button';
import { Loader2 } from 'lucide-react';
import { useCreateQuiz, useTestsForQuiz } from '@/lib/hooks/use-quiz';
import { getTextbooks, getChapters, getParagraphs } from '@/lib/api/content';
import { useQuery } from '@tanstack/react-query';
import { useClasses } from '@/lib/hooks/use-teacher-data';

interface QuizTest {
  id: number;
  title: string;
  description: string | null;
  question_count: number;
  difficulty: string;
}

export default function QuizCreateForm() {
  const t = useTranslations('quiz');
  const router = useRouter();

  const [classId, setClassId] = useState<number | undefined>();
  const [textbookId, setTextbookId] = useState<number | undefined>();
  const [chapterId, setChapterId] = useState<number | undefined>();
  const [paragraphId, setParagraphId] = useState<number | undefined>();
  const [testId, setTestId] = useState<number | undefined>();
  const [timeMs, setTimeMs] = useState(30000);
  const [shuffleQuestions, setShuffleQuestions] = useState(false);
  const [shuffleAnswers, setShuffleAnswers] = useState(false);
  const [scoringMode, setScoringMode] = useState<'speed' | 'accuracy'>('speed');
  const [mode, setMode] = useState<'classic' | 'team' | 'self_paced'>('classic');
  const [pacing, setPacing] = useState<'timed' | 'teacher_paced'>('timed');
  const [teamCount, setTeamCount] = useState(2);
  const [showSpaceRace, setShowSpaceRace] = useState(false);
  const [enablePowerups, setEnablePowerups] = useState(false);
  const [enableConfidence, setEnableConfidence] = useState(false);

  const { data: classes } = useClasses();
  const { data: textbooks } = useQuery({ queryKey: ['textbooks'], queryFn: getTextbooks });
  const { data: chapters } = useQuery({
    queryKey: ['chapters', textbookId],
    queryFn: () => getChapters(textbookId!),
    enabled: !!textbookId,
  });
  const { data: paragraphs } = useQuery({
    queryKey: ['paragraphs', chapterId],
    queryFn: () => getParagraphs(chapterId!),
    enabled: !!chapterId,
  });
  const { data: tests } = useTestsForQuiz({
    paragraph_id: paragraphId,
    chapter_id: !paragraphId ? chapterId : undefined,
  });

  const createQuiz = useCreateQuiz();

  const handleCreate = async () => {
    if (!testId) return;
    try {
      const result = await createQuiz.mutateAsync({
        test_id: testId,
        class_id: classId,
        settings: {
          time_per_question_ms: timeMs,
          shuffle_questions: shuffleQuestions,
          shuffle_answers: shuffleAnswers,
          scoring_mode: mode === 'self_paced' ? 'accuracy' : scoringMode,
          mode,
          pacing: mode === 'self_paced' ? 'timed' : pacing,
          ...(mode === 'team' ? { team_count: teamCount, show_space_race: showSpaceRace } : {}),
          ...(enablePowerups && pacing === 'timed' && mode !== 'self_paced' ? { enable_powerups: true } : {}),
          ...(enableConfidence && scoringMode === 'speed' && mode !== 'self_paced' ? { enable_confidence_mode: true } : {}),
        },
      });
      router.push(`/quiz/${result.id}`);
    } catch {
      // error handled by mutation
    }
  };

  const selectClass = 'w-full rounded-lg border bg-card px-3 py-2.5 text-sm';

  return (
    <div className="mx-auto max-w-lg space-y-6">
      {/* Class */}
      <div>
        <label className="mb-1.5 block text-sm font-medium">{t('selectClass')}</label>
        <select
          className={selectClass}
          value={classId || ''}
          onChange={(e) => setClassId(e.target.value ? Number(e.target.value) : undefined)}
        >
          <option value="">— {t('selectClass')} —</option>
          {(classes || []).map((c: { id: number; name: string }) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </div>

      {/* Textbook */}
      <div>
        <label className="mb-1.5 block text-sm font-medium">{t('selectTextbook')}</label>
        <select
          className={selectClass}
          value={textbookId || ''}
          onChange={(e) => { setTextbookId(Number(e.target.value) || undefined); setChapterId(undefined); setParagraphId(undefined); setTestId(undefined); }}
        >
          <option value="">—</option>
          {(textbooks || []).map((tb: { id: number; title: string }) => (
            <option key={tb.id} value={tb.id}>{tb.title}</option>
          ))}
        </select>
      </div>

      {/* Chapter */}
      {textbookId && (
        <div>
          <label className="mb-1.5 block text-sm font-medium">{t('selectChapter')}</label>
          <select
            className={selectClass}
            value={chapterId || ''}
            onChange={(e) => { setChapterId(Number(e.target.value) || undefined); setParagraphId(undefined); setTestId(undefined); }}
          >
            <option value="">—</option>
            {(chapters || []).map((ch: { id: number; title: string }) => (
              <option key={ch.id} value={ch.id}>{ch.title}</option>
            ))}
          </select>
        </div>
      )}

      {/* Paragraph */}
      {chapterId && (
        <div>
          <label className="mb-1.5 block text-sm font-medium">{t('selectParagraph')}</label>
          <select
            className={selectClass}
            value={paragraphId || ''}
            onChange={(e) => { setParagraphId(Number(e.target.value) || undefined); setTestId(undefined); }}
          >
            <option value="">— {t('allChapter')} —</option>
            {(paragraphs || []).map((p: { id: number; number: number; title: string }) => (
              <option key={p.id} value={p.id}>
                §{p.number}. {p.title}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Tests */}
      {(paragraphId || chapterId) && (
        <div>
          <label className="mb-1.5 block text-sm font-medium">{t('selectTest')}</label>
          {!tests || tests.length === 0 ? (
            <p className="text-sm text-muted-foreground">{t('noTests')}</p>
          ) : (
            <div className="space-y-2">
              {tests.map((test: QuizTest) => (
                <button
                  key={test.id}
                  onClick={() => setTestId(test.id)}
                  className={`w-full rounded-lg border p-3 text-left transition-colors ${
                    testId === test.id ? 'border-primary bg-primary/5' : 'hover:bg-muted/50'
                  }`}
                >
                  <span className="font-medium">{test.title}</span>
                  <span className="ml-2 text-sm text-muted-foreground">
                    {t('questions', { count: test.question_count })}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Game Mode */}
      {testId && (
        <div>
          <label className="mb-1.5 block text-sm font-medium">{t('gameMode')}</label>
          <select
            className={selectClass}
            value={mode}
            onChange={(e) => setMode(e.target.value as 'classic' | 'team' | 'self_paced')}
          >
            <option value="classic">{t('classicMode')}</option>
            <option value="team">{t('teamMode')}</option>
            <option value="self_paced">{t('selfPacedMode')}</option>
          </select>
        </div>
      )}

      {/* Team settings */}
      {testId && mode === 'team' && (
        <div className="space-y-3">
          <div>
            <label className="mb-1.5 block text-sm font-medium">{t('teamCount')}</label>
            <select
              className={selectClass}
              value={teamCount}
              onChange={(e) => setTeamCount(Number(e.target.value))}
            >
              {[2, 3, 4, 5, 6].map((n) => (
                <option key={n} value={n}>{n} {t('teams')}</option>
              ))}
            </select>
          </div>
          <label className="flex cursor-pointer items-center gap-2.5">
            <input
              type="checkbox"
              checked={showSpaceRace}
              onChange={(e) => setShowSpaceRace(e.target.checked)}
              className="h-4 w-4 rounded border-gray-300"
            />
            <span className="text-sm">{t('showSpaceRace')}</span>
          </label>
        </div>
      )}

      {/* Pacing */}
      {testId && mode !== 'self_paced' && (
        <div>
          <label className="mb-1.5 block text-sm font-medium">{t('pacing')}</label>
          <select
            className={selectClass}
            value={pacing}
            onChange={(e) => setPacing(e.target.value as 'timed' | 'teacher_paced')}
          >
            <option value="timed">{t('timedPacing')}</option>
            <option value="teacher_paced">{t('teacherPacedPacing')}</option>
          </select>
        </div>
      )}

      {/* Time */}
      {testId && mode !== 'self_paced' && pacing !== 'teacher_paced' && (
        <div>
          <label className="mb-1.5 block text-sm font-medium">{t('timePerQuestion')}</label>
          <select className={selectClass} value={timeMs} onChange={(e) => setTimeMs(Number(e.target.value))}>
            <option value={15000}>{t('seconds', { sec: 15 })}</option>
            <option value={20000}>{t('seconds', { sec: 20 })}</option>
            <option value={30000}>{t('seconds', { sec: 30 })}</option>
            <option value={45000}>{t('seconds', { sec: 45 })}</option>
            <option value={60000}>{t('seconds', { sec: 60 })}</option>
          </select>
        </div>
      )}

      {/* Shuffle & Scoring */}
      {testId && (
        <div className="space-y-4">
          <div>
            <label className="mb-2 block text-sm font-medium">{t('settings')}</label>
            <div className="space-y-2">
              <label className="flex cursor-pointer items-center gap-2.5">
                <input
                  type="checkbox"
                  checked={shuffleQuestions}
                  onChange={(e) => setShuffleQuestions(e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300"
                />
                <span className="text-sm">{t('shuffleQuestions')}</span>
              </label>
              <label className="flex cursor-pointer items-center gap-2.5">
                <input
                  type="checkbox"
                  checked={shuffleAnswers}
                  onChange={(e) => setShuffleAnswers(e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300"
                />
                <span className="text-sm">{t('shuffleAnswers')}</span>
              </label>
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium">{t('scoringMode')}</label>
            <select className={selectClass} value={scoringMode} onChange={(e) => setScoringMode(e.target.value as 'speed' | 'accuracy')}>
              <option value="speed">{t('speedMode')}</option>
              <option value="accuracy">{t('accuracyMode')}</option>
            </select>
          </div>

          {/* Power-ups toggle (only timed, classic/team) */}
          {pacing === 'timed' && mode !== 'self_paced' && (
            <label className="flex cursor-pointer items-center gap-2.5">
              <input
                type="checkbox"
                checked={enablePowerups}
                onChange={(e) => setEnablePowerups(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300"
              />
              <div>
                <span className="text-sm">{t('enablePowerups')}</span>
                <p className="text-xs text-muted-foreground">{t('powerupsHint')}</p>
              </div>
            </label>
          )}

          {/* Confidence mode toggle (only speed scoring, not self-paced) */}
          {scoringMode === 'speed' && mode !== 'self_paced' && (
            <label className="flex cursor-pointer items-center gap-2.5">
              <input
                type="checkbox"
                checked={enableConfidence}
                onChange={(e) => setEnableConfidence(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300"
              />
              <div>
                <span className="text-sm">{t('enableConfidence')}</span>
                <p className="text-xs text-muted-foreground">{t('confidenceHint')}</p>
              </div>
            </label>
          )}
        </div>
      )}

      {/* Submit */}
      <Button onClick={handleCreate} disabled={!testId || createQuiz.isPending} className="w-full">
        {createQuiz.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
        {t('create')}
      </Button>
    </div>
  );
}
