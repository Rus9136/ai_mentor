'use client';

import { use, useEffect, useState, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { useQuizSession, useStartQuiz, useCancelQuiz, useQuizResults } from '@/lib/hooks/use-quiz';
import { useTeacherQuizWebSocket } from '@/lib/hooks/use-quiz-websocket';
import { Loader2 } from 'lucide-react';

import QuizLobbyTeacher from '@/components/quiz/QuizLobbyTeacher';
import QuizLiveProgress from '@/components/quiz/QuizLiveProgress';
import QuizResults from '@/components/quiz/QuizResults';

interface Params {
  id: string;
}

export default function QuizDetailPage({ params }: { params: Promise<Params> }) {
  const { id } = use(params);
  const sessionId = parseInt(id, 10);
  const t = useTranslations('quiz');

  const { data: session, isLoading } = useQuizSession(sessionId);
  const { data: results } = useQuizResults(sessionId);
  const startQuiz = useStartQuiz();
  const cancelQuiz = useCancelQuiz();

  const joinCode = session?.join_code || null;
  const { lastMessage, sendNextQuestion, sendFinishQuiz, connected } = useTeacherQuizWebSocket(
    session?.status === 'lobby' || session?.status === 'in_progress' ? joinCode : null
  );

  // Track live state from WS
  const [participantCount, setParticipantCount] = useState(0);
  const [answeredCount, setAnsweredCount] = useState(0);
  const [currentQuestion, setCurrentQuestion] = useState(0);

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
    const students = (session.participants || []).map((p: Record<string, unknown>) => ({
      student_name: p.student_name as string,
      answered: false, // Updated via WS in real usage
    }));

    return (
      <QuizLiveProgress
        currentQuestion={currentQuestion}
        totalQuestions={session.question_count}
        answeredCount={answeredCount}
        totalParticipants={participantCount}
        students={students}
        onNextQuestion={sendNextQuestion}
        onEndQuiz={handleEndQuiz}
      />
    );
  }

  if (status === 'finished' && results) {
    return (
      <QuizResults
        totalQuestions={results.total_questions}
        leaderboard={results.leaderboard}
        stats={results.stats}
      />
    );
  }

  if (status === 'cancelled') {
    return <div className="py-12 text-center text-muted-foreground">{t('cancelled')}</div>;
  }

  return null;
}
