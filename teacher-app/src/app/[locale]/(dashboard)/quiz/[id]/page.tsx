'use client';

import { use, useEffect, useState, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { useQuizSession, useStartQuiz, useCancelQuiz, useQuizResults } from '@/lib/hooks/use-quiz';
import { useTeacherQuizWebSocket } from '@/lib/hooks/use-quiz-websocket';
import { Loader2 } from 'lucide-react';

import QuizLobbyTeacher from '@/components/quiz/QuizLobbyTeacher';
import QuizLiveProgress from '@/components/quiz/QuizLiveProgress';
import QuizTeacherPacedProgress from '@/components/quiz/QuizTeacherPacedProgress';
import QuizLiveMatrix from '@/components/quiz/QuizLiveMatrix';
import QuizReportDownloads from '@/components/quiz/QuizReportDownloads';
import QuizResults from '@/components/quiz/QuizResults';
import QuizSelfPacedProgress from '@/components/quiz/QuizSelfPacedProgress';
import SpaceRaceTrack from '@/components/quiz/SpaceRaceTrack';

interface Params {
  id: string;
}

export default function QuizDetailPage({ params }: { params: Promise<Params> }) {
  const { id } = use(params);
  const sessionId = parseInt(id, 10);
  const t = useTranslations('quiz');

  const { data: session, isLoading } = useQuizSession(sessionId);
  const { data: results } = useQuizResults(sessionId, session?.status);
  const startQuiz = useStartQuiz();
  const cancelQuiz = useCancelQuiz();

  const joinCode = session?.join_code || null;
  const { lastMessage, sendNextQuestion, sendFinishQuiz, sendGoToQuestion, connected } = useTeacherQuizWebSocket(
    session?.status === 'lobby' || session?.status === 'in_progress' ? joinCode : null
  );

  // Track live state from WS
  const [participantCount, setParticipantCount] = useState(0);
  const [answeredCount, setAnsweredCount] = useState(0);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [questionClosed, setQuestionClosed] = useState(false);

  useEffect(() => {
    if (session) {
      setParticipantCount(session.participant_count || session.participants?.length || 0);
      setCurrentQuestion(session.current_question_index >= 0 ? session.current_question_index + 1 : 0);
    }
  }, [session]);

  useEffect(() => {
    if (!lastMessage) return;
    switch (lastMessage.type) {
      case 'participant_joined':
        setParticipantCount((lastMessage.data as { count: number }).count);
        break;
      case 'answer_progress':
        setAnsweredCount((lastMessage.data as { answered: number }).answered);
        break;
      case 'question':
        setCurrentQuestion(((lastMessage.data as { index: number }).index || 0) + 1);
        setAnsweredCount(0);
        setQuestionClosed(false);
        break;
      case 'question_auto_closed':
        setQuestionClosed(true);
        break;
    }
  }, [lastMessage]);

  const handleStart = useCallback(async () => {
    await startQuiz.mutateAsync(sessionId);
  }, [sessionId, startQuiz]);

  const handleCancel = useCallback(async () => {
    if (confirm(t('confirmEnd'))) {
      await cancelQuiz.mutateAsync(sessionId);
    }
  }, [sessionId, cancelQuiz, t]);

  const handleEndQuiz = useCallback(() => {
    if (confirm(t('confirmEnd'))) {
      sendFinishQuiz();
    }
  }, [sendFinishQuiz, t]);

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!session) {
    return <div className="py-12 text-center text-muted-foreground">Session not found</div>;
  }

  const status = session.status;

  if (status === 'lobby') {
    return (
      <QuizLobbyTeacher
        joinCode={session.join_code}
        participants={session.participants || []}
        onStart={handleStart}
        onCancel={handleCancel}
        isStarting={startQuiz.isPending}
      />
    );
  }

  if (status === 'in_progress') {
    const mode = session.settings?.mode || 'classic';
    const pacing = session.settings?.pacing || 'timed';

    // Self-paced mode: show student progress dashboard
    if (mode === 'self_paced') {
      return (
        <QuizSelfPacedProgress
          sessionId={sessionId}
          totalQuestions={session.question_count}
          onEndQuiz={handleEndQuiz}
          status={status}
        />
      );
    }

    // Teacher-paced mode: question navigation
    if (pacing === 'teacher_paced') {
      return (
        <QuizTeacherPacedProgress
          currentQuestion={currentQuestion}
          totalQuestions={session.question_count}
          answeredCount={answeredCount}
          totalParticipants={participantCount}
          onGoToQuestion={sendGoToQuestion}
          onNextQuestion={sendNextQuestion}
          onEndQuiz={handleEndQuiz}
        />
      );
    }

    const students = (session.participants || []).map((p: Record<string, unknown>) => ({
      student_name: p.student_name as string,
      answered: false,
    }));

    // Team mode with space race
    const showSpaceRace = mode === 'team' && session.settings?.show_space_race;
    const teamProgress = (lastMessage?.type === 'team_progress'
      ? (lastMessage.data as { teams: Array<{ id: number; name: string; color: string; correct_answers: number; total_score: number }> }).teams
      : session.teams?.map((t: { id: number; name: string; color: string; total_score: number; correct_answers: number }) => ({
          id: t.id, name: t.name, color: t.color, correct_answers: t.correct_answers, total_score: t.total_score,
        }))
    ) || [];

    return (
      <div className="space-y-6">
        {showSpaceRace && teamProgress.length > 0 && (
          <SpaceRaceTrack teams={teamProgress} totalQuestions={session.question_count} />
        )}
        <QuizLiveProgress
          currentQuestion={currentQuestion}
          totalQuestions={session.question_count}
          answeredCount={answeredCount}
          totalParticipants={participantCount}
          students={students}
          onNextQuestion={sendNextQuestion}
          onEndQuiz={handleEndQuiz}
          questionClosed={questionClosed}
          autoAdvance={session.settings?.auto_advance || false}
          autoAdvanceDelayMs={session.settings?.auto_advance_delay_ms || 5000}
        />
        <QuizLiveMatrix sessionId={sessionId} status={status} />
      </div>
    );
  }

  if (status === 'finished' && results) {
    return (
      <div className="space-y-6">
        <QuizResults
          totalQuestions={results.total_questions}
          leaderboard={results.leaderboard}
          stats={results.stats}
        />
        <QuizLiveMatrix sessionId={sessionId} status={status} />
        <QuizReportDownloads sessionId={sessionId} />
      </div>
    );
  }

  if (status === 'cancelled') {
    return <div className="py-12 text-center text-muted-foreground">{t('cancelled')}</div>;
  }

  return null;
}
