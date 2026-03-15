'use client';

import { useReducer, useEffect, useCallback, useRef, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Volume2, VolumeX } from 'lucide-react';
import { joinQuiz } from '@/lib/api/quiz';
import { useQuizWebSocket } from '@/lib/hooks/use-quiz-websocket';
import { useQuizSounds } from '@/lib/hooks/use-quiz-sounds';
import { QuizState } from '@/types/quiz';
import type {
  QuizQuestionData,
  QuizFinishedData,
  LeaderboardEntry,
  WsServerMessage,
} from '@/types/quiz';

import QuizJoinScreen from '@/components/quiz/QuizJoinScreen';
import QuizLobby from '@/components/quiz/QuizLobby';
import QuizQuestion from '@/components/quiz/QuizQuestion';
import QuizAnswered from '@/components/quiz/QuizAnswered';
import QuizQuestionResult from '@/components/quiz/QuizQuestionResult';
import QuizFinished from '@/components/quiz/QuizFinished';

// ── State ──

interface QuizPageState {
  quizState: QuizState;
  joinCode: string | null;
  sessionId: number | null;
  participantCount: number;
  totalQuestions: number;
  currentQuestion: QuizQuestionData | null;
  lastOptions: string[];
  answerScore: number | null;
  answerCorrect: boolean | null;
  answerStreakBonus: number;
  answerCurrentStreak: number;
  resultCorrectOption: number | null;
  resultStats: Record<string, number>;
  resultLeaderboard: LeaderboardEntry[];
  finishedData: QuizFinishedData | null;
  error: string | null;
}

type QuizAction =
  | { type: 'JOIN_SUCCESS'; joinCode: string; sessionId: number; participantCount: number }
  | { type: 'WS_MESSAGE'; msg: WsServerMessage }
  | { type: 'ANSWER_SUBMITTED' }
  | { type: 'ERROR'; error: string };

const initialState: QuizPageState = {
  quizState: QuizState.JOIN,
  joinCode: null,
  sessionId: null,
  participantCount: 0,
  totalQuestions: 0,
  currentQuestion: null,
  lastOptions: [],
  answerScore: null,
  answerCorrect: null,
  answerStreakBonus: 0,
  answerCurrentStreak: 0,
  resultCorrectOption: null,
  resultStats: {},
  resultLeaderboard: [],
  finishedData: null,
  error: null,
};

function reducer(state: QuizPageState, action: QuizAction): QuizPageState {
  switch (action.type) {
    case 'JOIN_SUCCESS':
      return {
        ...state,
        quizState: QuizState.LOBBY,
        joinCode: action.joinCode,
        sessionId: action.sessionId,
        participantCount: action.participantCount,
        error: null,
      };

    case 'ANSWER_SUBMITTED':
      return { ...state, quizState: QuizState.ANSWERED, answerScore: null, answerCorrect: null };

    case 'ERROR':
      return { ...state, error: action.error };

    case 'WS_MESSAGE': {
      const msg = action.msg;
      switch (msg.type) {
        case 'participant_joined':
          return { ...state, participantCount: msg.data.count };

        case 'quiz_started':
          return { ...state, totalQuestions: msg.data.total_questions };

        case 'question':
          return {
            ...state,
            quizState: QuizState.QUESTION,
            currentQuestion: msg.data,
            lastOptions: msg.data.options,
            answerScore: null,
            answerCorrect: null,
          };

        case 'answer_accepted':
          return {
            ...state,
            answerScore: msg.data.score,
            answerCorrect: msg.data.is_correct,
            answerStreakBonus: msg.data.streak_bonus || 0,
            answerCurrentStreak: msg.data.current_streak || 0,
          };

        case 'question_result':
          return {
            ...state,
            quizState: QuizState.RESULT,
            resultCorrectOption: msg.data.correct_option,
            resultStats: msg.data.stats,
            resultLeaderboard: msg.data.leaderboard_top5,
          };

        case 'quiz_finished':
          return {
            ...state,
            quizState: QuizState.FINISHED,
            finishedData: msg.data,
          };

        case 'error':
          return { ...state, error: msg.data.message };

        default:
          return state;
      }
    }

    default:
      return state;
  }
}

// ── Component ──

export default function QuizPage() {
  return (
    <Suspense fallback={<div className="flex min-h-dvh items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>}>
      <QuizPageInner />
    </Suspense>
  );
}

function QuizPageInner() {
  const searchParams = useSearchParams();
  const initialCode = searchParams.get('code') || undefined;

  const [state, dispatch] = useReducer(reducer, initialState);
  const { lastMessage, send } = useQuizWebSocket(state.joinCode);
  const { play, muted, toggleMute } = useQuizSounds();

  // ── Sound triggers on state transitions ──
  const prevQuizState = useRef(QuizState.JOIN);
  useEffect(() => {
    const prev = prevQuizState.current;
    const curr = state.quizState;
    prevQuizState.current = curr;
    if (prev === curr) return;

    switch (curr) {
      case QuizState.LOBBY:
        play('lobby');
        break;
      case QuizState.QUESTION:
        play('questionAppear');
        break;
      case QuizState.RESULT:
        play('result');
        break;
      case QuizState.FINISHED:
        play('victory');
        break;
    }
  }, [state.quizState, play]);

  // Sound on correct / incorrect / streak
  useEffect(() => {
    if (state.answerCorrect === true) {
      play('correct');
      if (state.answerStreakBonus > 0) {
        setTimeout(() => play('streak'), 300);
      }
    } else if (state.answerCorrect === false) {
      play('incorrect');
    }
  }, [state.answerCorrect, state.answerStreakBonus, play]);

  const playTick = useCallback(() => play('tick'), [play]);
  const playTimeUp = useCallback(() => play('timeUp'), [play]);

  // Process WS messages
  useEffect(() => {
    if (lastMessage) {
      dispatch({ type: 'WS_MESSAGE', msg: lastMessage });
    }
  }, [lastMessage]);

  // Auto-join from URL code
  useEffect(() => {
    if (initialCode && state.quizState === QuizState.JOIN) {
      handleJoin(initialCode);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleJoin = async (code: string) => {
    try {
      const result = await joinQuiz(code);
      dispatch({
        type: 'JOIN_SUCCESS',
        joinCode: code,
        sessionId: result.quiz_session_id,
        participantCount: result.participant_count,
      });
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Failed to join';
      throw new Error(message);
    }
  };

  const handleAnswer = useCallback(
    (selectedOption: number, answerTimeMs: number) => {
      if (!state.currentQuestion) return;
      dispatch({ type: 'ANSWER_SUBMITTED' });
      send({
        type: 'answer',
        data: {
          question_index: state.currentQuestion.index,
          selected_option: selectedOption,
          answer_time_ms: answerTimeMs,
        },
      });
    },
    [state.currentQuestion, send],
  );

  // ── Render ──

  const muteButton = state.quizState !== QuizState.JOIN && (
    <button
      onClick={toggleMute}
      className="fixed right-3 top-3 z-50 flex h-9 w-9 items-center justify-center rounded-full bg-black/20 backdrop-blur-sm text-white/70 hover:text-white transition-colors"
      aria-label={muted ? 'Unmute' : 'Mute'}
    >
      {muted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
    </button>
  );

  const renderScreen = () => {
    switch (state.quizState) {
      case QuizState.JOIN:
        return <QuizJoinScreen onJoin={handleJoin} initialCode={initialCode} />;

      case QuizState.LOBBY:
        return <QuizLobby participantCount={state.participantCount} />;

      case QuizState.QUESTION:
        return state.currentQuestion ? (
          <QuizQuestion
            question={state.currentQuestion}
            questionNumber={state.currentQuestion.index + 1}
            totalQuestions={state.totalQuestions}
            onAnswer={handleAnswer}
            onTimerTick={playTick}
            onTimeUp={playTimeUp}
          />
        ) : null;

      case QuizState.ANSWERED:
        return (
          <QuizAnswered
            score={state.answerScore}
            isCorrect={state.answerCorrect}
            streakBonus={state.answerStreakBonus}
            currentStreak={state.answerCurrentStreak}
          />
        );

      case QuizState.RESULT:
        return (
          <QuizQuestionResult
            correctOption={state.resultCorrectOption}
            stats={state.resultStats}
            options={state.lastOptions}
            leaderboardTop5={state.resultLeaderboard}
          />
        );

      case QuizState.FINISHED:
        return state.finishedData ? <QuizFinished data={state.finishedData} /> : null;

      default:
        return null;
    }
  };

  return (
    <>
      {muteButton}
      {renderScreen()}
    </>
  );
}
