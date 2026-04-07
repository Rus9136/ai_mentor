'use client';

import { useReducer, useEffect, useCallback, useRef, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Volume2, VolumeX } from 'lucide-react';
import { joinQuiz, getNextQuestion, submitSelfPacedAnswer } from '@/lib/api/quiz';
import { getAccessToken } from '@/lib/api/client';
import { useQuizWebSocket } from '@/lib/hooks/use-quiz-websocket';
import { useQuizSounds } from '@/lib/hooks/use-quiz-sounds';
import { QuizState } from '@/types/quiz';
import type {
  QuizQuestionData,
  QuizFinishedData,
  LeaderboardEntry,
  TeamEntry,
  WsServerMessage,
  SelfPacedAnswerResult,
} from '@/types/quiz';

import QuizJoinScreen from '@/components/quiz/QuizJoinScreen';
import QuizLobby from '@/components/quiz/QuizLobby';
import QuizQuestion from '@/components/quiz/QuizQuestion';
import QuizAnswered from '@/components/quiz/QuizAnswered';
import QuizQuestionResult from '@/components/quiz/QuizQuestionResult';
import QuizFinished from '@/components/quiz/QuizFinished';
import QuizSelfPacedFeedback from '@/components/quiz/QuizSelfPacedFeedback';
import QuizShortAnswer from '@/components/quiz/QuizShortAnswer';
import QuizQuickAnswer from '@/components/quiz/QuizQuickAnswer';
import QuizPowerupBar from '@/components/quiz/QuizPowerupBar';
import QuizConfidenceChoice from '@/components/quiz/QuizConfidenceChoice';

// ── State ──

interface QuizPageState {
  quizState: QuizState;
  joinCode: string | null;
  sessionId: number | null;
  mode: string;
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
  // Team mode
  teamName: string | null;
  teamColor: string | null;
  teamLeaderboard: TeamEntry[];
  // Quick question
  quickQuestionText: string | null;
  quickQuestionOptions: string[];
  // Self-paced
  selfPacedFeedback: SelfPacedAnswerResult | null;
  // Power-up effects on last answer
  answerPowerupUsed: string | null;
  answerScoreDoubled: boolean;
  answerStreakProtected: boolean;
  // Power-ups (Phase 2.4)
  activePowerup: string | null;
  removedOptions: number[] | null;
  extraTimeMs: number;
  studentXp: number;
  enablePowerups: boolean;
  // Confidence mode (Phase 2.4)
  enableConfidence: boolean;
  confidenceChoice: 'risk' | 'safe' | null;
  // Auto-advance (Phase 2.4.5)
  autoAdvanceMs: number | null;
}

type QuizAction =
  | { type: 'JOIN_SUCCESS'; joinCode: string; sessionId: number; participantCount: number; mode?: string; teamName?: string; teamColor?: string }
  | { type: 'WS_MESSAGE'; msg: WsServerMessage }
  | { type: 'ANSWER_SUBMITTED' }
  | { type: 'SELF_PACED_QUESTION'; question: QuizQuestionData; answeredCount: number; totalQuestions: number }
  | { type: 'SELF_PACED_FEEDBACK'; result: SelfPacedAnswerResult }
  | { type: 'SELF_PACED_FINISHED' }
  | { type: 'QUICK_ANSWERED' }
  | { type: 'CONFIDENCE_CHOICE'; choice: 'risk' | 'safe' }
  | { type: 'SET_STUDENT_XP'; xp: number }
  | { type: 'SET_QUIZ_SETTINGS'; enablePowerups: boolean; enableConfidence: boolean }
  | { type: 'ERROR'; error: string };

const initialState: QuizPageState = {
  quizState: QuizState.JOIN,
  joinCode: null,
  sessionId: null,
  mode: 'classic',
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
  teamName: null,
  teamColor: null,
  teamLeaderboard: [],
  quickQuestionText: null,
  quickQuestionOptions: [],
  selfPacedFeedback: null,
  answerPowerupUsed: null,
  answerScoreDoubled: false,
  answerStreakProtected: false,
  activePowerup: null,
  removedOptions: null,
  extraTimeMs: 0,
  studentXp: 0,
  enablePowerups: false,
  enableConfidence: false,
  confidenceChoice: null,
  autoAdvanceMs: null,
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
        mode: action.mode || 'classic',
        teamName: action.teamName || null,
        teamColor: action.teamColor || null,
        error: null,
      };

    case 'ANSWER_SUBMITTED':
      return { ...state, quizState: QuizState.ANSWERED, answerScore: null, answerCorrect: null };

    case 'SELF_PACED_QUESTION':
      return {
        ...state,
        quizState: QuizState.SELF_PACED_QUESTION,
        currentQuestion: action.question,
        lastOptions: action.question.options,
        totalQuestions: action.totalQuestions,
      };

    case 'SELF_PACED_FEEDBACK':
      return {
        ...state,
        quizState: QuizState.SELF_PACED_FEEDBACK,
        selfPacedFeedback: action.result,
      };

    case 'SELF_PACED_FINISHED':
      return { ...state, quizState: QuizState.FINISHED };

    case 'QUICK_ANSWERED':
      return { ...state, quizState: QuizState.QUICK_WAITING };

    case 'CONFIDENCE_CHOICE':
      return { ...state, confidenceChoice: action.choice };

    case 'SET_STUDENT_XP':
      return { ...state, studentXp: action.xp };

    case 'SET_QUIZ_SETTINGS':
      return { ...state, enablePowerups: action.enablePowerups, enableConfidence: action.enableConfidence };

    case 'ERROR':
      return { ...state, error: action.error };

    case 'WS_MESSAGE': {
      const msg = action.msg;
      switch (msg.type) {
        case 'participant_joined':
          return { ...state, participantCount: msg.data.count };

        case 'quiz_started':
          return {
            ...state,
            totalQuestions: msg.data.total_questions,
            enablePowerups: msg.data.enable_powerups || false,
            enableConfidence: msg.data.enable_confidence_mode || false,
          };

        case 'question':
          return {
            ...state,
            quizState: QuizState.QUESTION,
            currentQuestion: msg.data,
            lastOptions: msg.data.options,
            answerScore: null,
            answerCorrect: null,
            // Reset power-up, confidence, and auto-advance for new question
            activePowerup: null,
            removedOptions: null,
            extraTimeMs: 0,
            confidenceChoice: null,
            autoAdvanceMs: null,
          };

        case 'answer_accepted':
          return {
            ...state,
            answerScore: msg.data.score,
            answerCorrect: msg.data.is_correct,
            answerStreakBonus: msg.data.streak_bonus || 0,
            answerCurrentStreak: msg.data.current_streak || 0,
            answerPowerupUsed: msg.data.powerup_used || null,
            answerScoreDoubled: msg.data.score_doubled || false,
            answerStreakProtected: msg.data.streak_protected || false,
          };

        case 'question_result':
          return {
            ...state,
            quizState: QuizState.RESULT,
            resultCorrectOption: msg.data.correct_option,
            resultStats: msg.data.stats,
            resultLeaderboard: msg.data.leaderboard_top5,
            autoAdvanceMs: msg.data.auto_advance_ms ?? null,
          };

        case 'quiz_finished':
          return {
            ...state,
            quizState: QuizState.FINISHED,
            finishedData: msg.data,
          };

        case 'team_assigned':
          return {
            ...state,
            teamName: msg.data.team_name,
            teamColor: msg.data.team_color,
          };

        case 'team_leaderboard':
          return {
            ...state,
            teamLeaderboard: msg.data.teams,
          };

        case 'quick_question':
          return {
            ...state,
            quizState: QuizState.QUICK_ANSWER,
            quickQuestionText: msg.data.question_text,
            quickQuestionOptions: msg.data.options,
          };

        case 'quick_answer_accepted':
          return { ...state, quizState: QuizState.QUICK_WAITING };

        case 'quick_question_end':
          return {
            ...state,
            quizState: QuizState.LOBBY,
            quickQuestionText: null,
            quickQuestionOptions: [],
          };

        case 'powerup_activated':
          return {
            ...state,
            activePowerup: msg.data.powerup_type,
            studentXp: msg.data.xp_remaining,
            removedOptions: msg.data.removed_options || null,
            extraTimeMs: msg.data.extra_time_ms || 0,
          };

        case 'powerup_error':
          return { ...state, error: msg.data.message };

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
  const [selfPacedLoading, setSelfPacedLoading] = useState(false);

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
      case QuizState.SELF_PACED_QUESTION:
        play('questionAppear');
        break;
      case QuizState.RESULT:
        play('result');
        break;
      case QuizState.FINISHED:
        // Podium component handles its own sounds when 3+ participants
        if (!state.finishedData || state.finishedData.leaderboard.length < 3) {
          play('victory');
        }
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

  // Self-paced: fetch first question after quiz_started
  useEffect(() => {
    if (state.mode === 'self_paced' && state.totalQuestions > 0 && state.quizState === QuizState.LOBBY && state.sessionId) {
      fetchNextSelfPacedQuestion();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.totalQuestions, state.mode]);

  // Auto-join from URL code
  useEffect(() => {
    if (initialCode && state.quizState === QuizState.JOIN) {
      handleJoin(initialCode);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleJoin = async (code: string) => {
    try {
      // Ensure token is in localStorage before API call.
      // TokenExtractor in webview/layout.tsx may not have resolved yet
      // (Suspense + useSearchParams race condition), so read directly from URL.
      if (!getAccessToken()) {
        const token = searchParams.get('token');
        if (token) {
          localStorage.setItem('ai_mentor_access_token', token);
        }
      }
      const result = await joinQuiz(code);
      dispatch({
        type: 'JOIN_SUCCESS',
        joinCode: code,
        sessionId: result.quiz_session_id,
        participantCount: result.participant_count,
        mode: result.mode,
        teamName: result.team_name,
        teamColor: result.team_color,
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
      const data: Record<string, unknown> = {
        question_index: state.currentQuestion.index,
        selected_option: selectedOption,
        answer_time_ms: answerTimeMs,
      };
      if (state.confidenceChoice) {
        data.confidence_mode = state.confidenceChoice;
      }
      send({ type: 'answer', data });
    },
    [state.currentQuestion, state.confidenceChoice, send],
  );

  const handleShortAnswer = useCallback(
    (textAnswer: string, answerTimeMs: number) => {
      if (!state.currentQuestion) return;
      dispatch({ type: 'ANSWER_SUBMITTED' });
      const data: Record<string, unknown> = {
        question_index: state.currentQuestion.index,
        text_answer: textAnswer,
        answer_time_ms: answerTimeMs,
      };
      if (state.confidenceChoice) {
        data.confidence_mode = state.confidenceChoice;
      }
      send({ type: 'answer', data });
    },
    [state.currentQuestion, state.confidenceChoice, send],
  );

  // ── Self-paced handlers ──

  const fetchNextSelfPacedQuestion = async () => {
    if (!state.sessionId) return;
    setSelfPacedLoading(true);
    try {
      const data = await getNextQuestion(state.sessionId);
      dispatch({
        type: 'SELF_PACED_QUESTION',
        question: data.question,
        answeredCount: data.answered_count,
        totalQuestions: data.total_questions,
      });
    } catch {
      dispatch({ type: 'SELF_PACED_FINISHED' });
    } finally {
      setSelfPacedLoading(false);
    }
  };

  const handleSelfPacedAnswer = async (selectedOption: number) => {
    if (!state.sessionId || !state.currentQuestion) return;
    setSelfPacedLoading(true);
    try {
      const result = await submitSelfPacedAnswer(
        state.sessionId,
        state.currentQuestion.index,
        selectedOption,
      );
      if (result.is_correct) play('correct');
      else play('incorrect');
      dispatch({ type: 'SELF_PACED_FEEDBACK', result });
    } catch (e: unknown) {
      dispatch({ type: 'ERROR', error: e instanceof Error ? e.message : 'Error submitting answer' });
    } finally {
      setSelfPacedLoading(false);
    }
  };

  const handleSelfPacedNext = () => {
    if (state.selfPacedFeedback?.is_finished) {
      dispatch({ type: 'SELF_PACED_FINISHED' });
    } else {
      fetchNextSelfPacedQuestion();
    }
  };

  // ── Power-up handler ──

  const handleActivatePowerup = useCallback(
    (powerupType: string) => {
      send({ type: 'activate_powerup', data: { powerup_type: powerupType } });
      play('powerupActivate');
    },
    [send, play],
  );

  // ── Confidence choice handler ──

  const handleConfidenceChoice = useCallback(
    (choice: 'risk' | 'safe') => {
      dispatch({ type: 'CONFIDENCE_CHOICE', choice });
    },
    [],
  );

  // ── Quick question handler ──

  const handleQuickAnswer = (selectedOption: number) => {
    send({ type: 'quick_answer', data: { selected_option: selectedOption } });
    dispatch({ type: 'QUICK_ANSWERED' });
  };

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
        return (
          <QuizLobby
            participantCount={state.participantCount}
            teamName={state.teamName}
            teamColor={state.teamColor}
          />
        );

      case QuizState.QUESTION:
        if (!state.currentQuestion) return null;
        if (state.currentQuestion.question_type === 'short_answer') {
          return (
            <>
              {state.enableConfidence && (
                <QuizConfidenceChoice onChoice={handleConfidenceChoice} chosen={state.confidenceChoice} />
              )}
              <QuizShortAnswer
                question={state.currentQuestion}
                questionNumber={state.currentQuestion.index + 1}
                totalQuestions={state.totalQuestions}
                onAnswer={handleShortAnswer}
                onTimerTick={playTick}
                onTimeUp={playTimeUp}
                hideTimer={state.currentQuestion.time_limit_ms === 0}
              />
            </>
          );
        }
        return (
          <>
            {state.enablePowerups && (
              <QuizPowerupBar
                studentXp={state.studentXp}
                activePowerup={state.activePowerup}
                onActivate={handleActivatePowerup}
                enabled={state.enablePowerups}
              />
            )}
            {state.enableConfidence && (
              <QuizConfidenceChoice onChoice={handleConfidenceChoice} chosen={state.confidenceChoice} />
            )}
            <QuizQuestion
              question={state.currentQuestion}
              questionNumber={state.currentQuestion.index + 1}
              totalQuestions={state.totalQuestions}
              onAnswer={handleAnswer}
              onTimerTick={playTick}
              onTimeUp={playTimeUp}
              hideTimer={state.currentQuestion.time_limit_ms === 0}
              removedOptions={state.removedOptions}
              extraTimeMs={state.extraTimeMs}
              disableAnswers={state.enableConfidence && !state.confidenceChoice}
            />
          </>
        );

      case QuizState.ANSWERED:
        return (
          <QuizAnswered
            score={state.answerScore}
            isCorrect={state.answerCorrect}
            streakBonus={state.answerStreakBonus}
            currentStreak={state.answerCurrentStreak}
            powerupUsed={state.answerPowerupUsed}
            scoreDoubled={state.answerScoreDoubled}
            streakProtected={state.answerStreakProtected}
          />
        );

      case QuizState.RESULT:
        return (
          <QuizQuestionResult
            correctOption={state.resultCorrectOption}
            stats={state.resultStats}
            options={state.lastOptions}
            leaderboardTop5={state.resultLeaderboard}
            teamLeaderboard={state.teamLeaderboard}
            autoAdvanceMs={state.autoAdvanceMs}
          />
        );

      case QuizState.FINISHED:
        return state.finishedData ? (
          <QuizFinished
            data={state.finishedData}
            onPlaySound={(s) => play(s as Parameters<typeof play>[0])}
          />
        ) : null;

      // Self-paced states
      case QuizState.SELF_PACED_QUESTION:
        return state.currentQuestion ? (
          <QuizQuestion
            question={state.currentQuestion}
            questionNumber={state.currentQuestion.index + 1}
            totalQuestions={state.totalQuestions}
            onAnswer={(opt) => handleSelfPacedAnswer(opt)}
            hideTimer
          />
        ) : null;

      case QuizState.SELF_PACED_FEEDBACK:
        return state.selfPacedFeedback ? (
          <QuizSelfPacedFeedback
            result={state.selfPacedFeedback}
            options={state.lastOptions}
            onNext={handleSelfPacedNext}
            loading={selfPacedLoading}
          />
        ) : null;

      // Quick question states
      case QuizState.QUICK_ANSWER:
        return state.quickQuestionText ? (
          <QuizQuickAnswer
            questionText={state.quickQuestionText}
            options={state.quickQuestionOptions}
            onAnswer={handleQuickAnswer}
          />
        ) : null;

      case QuizState.QUICK_WAITING:
        return (
          <div className="flex min-h-dvh flex-col items-center justify-center px-4 text-center">
            <div className="mb-4 text-4xl">✓</div>
            <p className="text-lg font-medium text-foreground">Ответ принят</p>
            <p className="mt-2 text-sm text-muted-foreground">Ожидайте следующий вопрос...</p>
          </div>
        );

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
