'use client';

import { useEffect, useState, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { Button } from '@/components/ui/button';
import { Check, X, Eye, SkipForward, Trophy, Users } from 'lucide-react';

interface CellState {
  points: number;
  status: 'available' | 'active' | 'answered' | 'skipped';
  answered_by_team_id?: number | null;
}

interface CategoryState {
  name: string;
  cells: CellState[];
}

interface TeamScore {
  id: number;
  name: string;
  color: string;
  score: number;
  correct_answers: number;
}

interface BoardData {
  categories: CategoryState[];
  team_scores: TeamScore[];
  current_team_index: number;
  current_team_name: string;
  cells_remaining: number;
  active_cell?: { category: number; row: number } | null;
  pass_to_other?: boolean;
}

interface QuestionData {
  text: string;
  options: string[];
  question_type: string;
  image_url?: string | null;
}

interface CellSelectedData {
  category_index: number;
  category_name: string;
  row_index: number;
  points: number;
  question: QuestionData;
  team_name: string;
}

interface JudgeResultData {
  is_correct: boolean;
  points: number;
  team_name: string;
  team_scores: TeamScore[];
  next_team_name: string;
  pass_to_other: boolean;
  cells_remaining: number;
}

interface AnswerRevealedData {
  correct_option: number | null;
  correct_text: string;
}

interface FactileFinishedData {
  team_scores: TeamScore[];
  winner_team_name: string;
  winner_team_id: number;
  leaderboard?: Array<{ rank: number; student_name: string; total_score: number; xp_earned: number }>;
}

interface WsMessage {
  type: string;
  data: Record<string, unknown>;
}

interface FactileBoardProps {
  sessionId: number;
  lastMessage: WsMessage | null;
  initialBoardState?: BoardData | null;
  onSelectCell: (category: number, row: number) => void;
  onJudgeCorrect: () => void;
  onJudgeWrong: () => void;
  onRevealAnswer: () => void;
  onSkipCell: () => void;
  onFinishQuiz: () => void;
}

const OPTION_LABELS = ['A', 'B', 'C', 'D', 'E', 'F'];

export default function FactileBoard({
  lastMessage, initialBoardState, onSelectCell, onJudgeCorrect, onJudgeWrong,
  onRevealAnswer, onSkipCell, onFinishQuiz,
}: FactileBoardProps) {
  const t = useTranslations('quiz');

  const [board, setBoard] = useState<BoardData | null>(initialBoardState || null);
  const [activeQuestion, setActiveQuestion] = useState<CellSelectedData | null>(null);
  const [revealedAnswer, setRevealedAnswer] = useState<AnswerRevealedData | null>(null);
  const [lastJudge, setLastJudge] = useState<JudgeResultData | null>(null);
  const [finished, setFinished] = useState<FactileFinishedData | null>(null);
  const [passToOther, setPassToOther] = useState(false);

  // Handle WS messages
  useEffect(() => {
    if (!lastMessage) return;

    switch (lastMessage.type) {
      case 'factile_board':
        setBoard(lastMessage.data as unknown as BoardData);
        setPassToOther((lastMessage.data as unknown as BoardData).pass_to_other || false);
        break;

      case 'cell_selected':
        setActiveQuestion(lastMessage.data as unknown as CellSelectedData);
        setRevealedAnswer(null);
        setLastJudge(null);
        break;

      case 'judge_result': {
        const jr = lastMessage.data as unknown as JudgeResultData;
        setLastJudge(jr);
        setPassToOther(jr.pass_to_other);
        if (!jr.pass_to_other) {
          // Cell is closed — clear active question
          setActiveQuestion(null);
          setRevealedAnswer(null);
        }
        break;
      }

      case 'answer_revealed':
        setRevealedAnswer(lastMessage.data as unknown as AnswerRevealedData);
        break;

      case 'cell_skipped':
        setActiveQuestion(null);
        setRevealedAnswer(null);
        setLastJudge(null);
        break;

      case 'factile_finished':
        setFinished(lastMessage.data as unknown as FactileFinishedData);
        break;
    }
  }, [lastMessage]);

  const handleCellClick = useCallback((catIdx: number, rowIdx: number) => {
    if (activeQuestion) return; // A cell is already open
    onSelectCell(catIdx, rowIdx);
  }, [activeQuestion, onSelectCell]);

  // ── Finished screen ──
  if (finished) {
    return (
      <div className="space-y-6">
        <div className="rounded-xl border bg-card p-8 text-center">
          <Trophy className="mx-auto h-16 w-16 text-yellow-500 mb-4" />
          <h2 className="text-3xl font-bold mb-2">{finished.winner_team_name}</h2>
          <p className="text-muted-foreground">{t('factileWinner')}</p>
        </div>

        {/* Team scores */}
        <div className="grid grid-cols-2 gap-4">
          {finished.team_scores.map((team) => (
            <div
              key={team.id}
              className="rounded-xl border-2 p-6 text-center"
              style={{ borderColor: team.color }}
            >
              <p className="text-lg font-bold" style={{ color: team.color }}>{team.name}</p>
              <p className="text-4xl font-black mt-2">{team.score}</p>
              <p className="text-sm text-muted-foreground mt-1">
                {team.correct_answers} {t('correctAnswers').toLowerCase()}
              </p>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!board) {
    return <div className="py-12 text-center text-muted-foreground">{t('loadingBoard')}</div>;
  }

  return (
    <div className="space-y-4">
      {/* Team scores bar */}
      <div className="flex gap-3">
        {board.team_scores.map((team, idx) => (
          <div
            key={team.id}
            className={`flex-1 rounded-xl border-2 p-3 text-center transition-all ${
              board.current_team_index === idx ? 'ring-2 ring-offset-2 shadow-lg scale-[1.02]' : 'opacity-75'
            }`}
            style={{
              borderColor: team.color,
              ...(board.current_team_index === idx ? { ringColor: team.color } : {}),
            }}
          >
            <div className="flex items-center justify-center gap-2">
              <Users className="h-4 w-4" />
              <span className="font-bold" style={{ color: team.color }}>{team.name}</span>
              {board.current_team_index === idx && (
                <span className="ml-1 rounded-full bg-primary px-2 py-0.5 text-[10px] font-medium text-primary-foreground">
                  {passToOther ? t('factileSteal') : t('factileTurn')}
                </span>
              )}
            </div>
            <p className="text-3xl font-black mt-1">{team.score}</p>
          </div>
        ))}
      </div>

      {/* Active question overlay */}
      {activeQuestion && (
        <div className="rounded-xl border-2 border-primary bg-card p-6 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm font-medium text-muted-foreground">
              {activeQuestion.category_name} — {activeQuestion.points} {t('points')}
            </span>
            <span className="rounded-full px-3 py-1 text-xs font-bold text-white"
              style={{ backgroundColor: board.team_scores[board.current_team_index]?.color || '#666' }}>
              {passToOther
                ? `${board.team_scores[board.current_team_index]?.name} ${t('factileCanSteal')}`
                : `${activeQuestion.team_name}`
              }
            </span>
          </div>

          <h3 className="text-xl font-bold mb-4">{activeQuestion.question.text}</h3>

          {/* Options */}
          <div className="grid gap-2 mb-6">
            {activeQuestion.question.options.map((opt, i) => (
              <div
                key={i}
                className={`flex items-center gap-3 rounded-lg border p-3 ${
                  revealedAnswer && revealedAnswer.correct_option === i
                    ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
                    : ''
                }`}
              >
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted font-bold text-sm">
                  {OPTION_LABELS[i]}
                </span>
                <span className="text-sm">{opt}</span>
                {revealedAnswer && revealedAnswer.correct_option === i && (
                  <Check className="ml-auto h-5 w-5 text-green-600" />
                )}
              </div>
            ))}
          </div>

          {/* Judge result feedback */}
          {lastJudge && (
            <div className={`mb-4 rounded-lg p-3 text-center font-medium ${
              lastJudge.is_correct
                ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
            }`}>
              {lastJudge.is_correct
                ? `✓ ${lastJudge.team_name} +${lastJudge.points}`
                : lastJudge.pass_to_other
                  ? `✗ ${lastJudge.team_name} — ${lastJudge.next_team_name} ${t('factileCanAnswer')}`
                  : `✗ ${t('factileNoOneCorrect')}`
              }
            </div>
          )}

          {/* Teacher controls */}
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => { console.log('judge_correct clicked'); onJudgeCorrect(); }} className="gap-2 bg-green-600 hover:bg-green-700">
              <Check className="h-4 w-4" /> {t('factileCorrect')}
            </Button>
            <Button onClick={() => { console.log('judge_wrong clicked'); onJudgeWrong(); }} variant="destructive" className="gap-2">
              <X className="h-4 w-4" /> {t('factileWrong')}
            </Button>
            <Button onClick={() => { console.log('reveal_answer clicked'); onRevealAnswer(); }} variant="outline" className="gap-2">
              <Eye className="h-4 w-4" /> {t('factileReveal')}
            </Button>
            <Button onClick={() => { console.log('skip_cell clicked'); onSkipCell(); }} variant="secondary" className="gap-2">
              <SkipForward className="h-4 w-4" /> {t('factileSkip')}
            </Button>
          </div>
        </div>
      )}

      {/* Board grid */}
      {!activeQuestion && (
        <div className="overflow-x-auto">
          <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(${board.categories.length}, minmax(120px, 1fr))` }}>
            {/* Category headers */}
            {board.categories.map((cat, catIdx) => (
              <div key={catIdx} className="rounded-lg bg-primary p-3 text-center">
                <span className="text-sm font-bold text-primary-foreground">{cat.name}</span>
              </div>
            ))}

            {/* Cells — iterate by rows */}
            {board.categories[0]?.cells.map((_, rowIdx) => (
              board.categories.map((cat, catIdx) => {
                const cell = cat.cells[rowIdx];
                if (!cell) return <div key={`${catIdx}-${rowIdx}`} />;

                const isAvailable = cell.status === 'available';
                const isAnswered = cell.status === 'answered' || cell.status === 'skipped';
                const teamColor = cell.answered_by_team_id
                  ? board.team_scores.find(t => t.id === cell.answered_by_team_id)?.color
                  : undefined;

                return (
                  <button
                    key={`${catIdx}-${rowIdx}`}
                    onClick={() => isAvailable && handleCellClick(catIdx, rowIdx)}
                    disabled={!isAvailable}
                    className={`rounded-lg border-2 p-4 text-center font-bold text-xl transition-all ${
                      isAvailable
                        ? 'border-primary/30 bg-primary/5 hover:bg-primary/15 hover:border-primary hover:scale-105 cursor-pointer shadow-sm'
                        : isAnswered
                          ? 'border-transparent opacity-30 cursor-default'
                          : 'border-muted cursor-default'
                    }`}
                    style={teamColor && isAnswered ? { borderColor: teamColor, opacity: 0.4 } : {}}
                  >
                    {isAvailable ? cell.points : isAnswered ? '—' : cell.points}
                  </button>
                );
              })
            ))}
          </div>
        </div>
      )}

      {/* Bottom controls */}
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground">
          {t('factileCellsLeft', { count: board.cells_remaining })}
        </span>
        <Button variant="outline" onClick={onFinishQuiz}>
          {t('endGame')}
        </Button>
      </div>
    </div>
  );
}
