'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useTranslations, useLocale } from 'next-intl';
import { ArrowLeft, Loader2, CheckCircle2, Clock } from 'lucide-react';
import { Link } from '@/i18n/routing';
import {
  useHomeworkDetail,
  useTaskQuestions,
  useStartTask,
  useSubmitAnswer,
  useCompleteSubmission,
} from '@/lib/hooks/use-homework';
import {
  StudentQuestionResponse,
  QuestionType,
  SubmissionStatus,
  SubmissionResult,
  TaskType,
} from '@/lib/api/homework';
import {
  ChoiceQuestion,
  TextQuestion,
  QuestionFeedback,
  SubmissionResultCard,
} from '@/components/homework';
import { cn } from '@/lib/utils';

interface AnsweredQuestion {
  question: StudentQuestionResponse;
  feedback: SubmissionResult;
}

type TaskState = 'loading' | 'not_started' | 'in_progress' | 'completed';

export default function TaskExecutionPage() {
  const params = useParams();
  const router = useRouter();
  const t = useTranslations('homework');
  const locale = useLocale();

  const homeworkId = params.id ? Number(params.id) : undefined;
  const taskId = params.taskId ? Number(params.taskId) : undefined;

  // State
  const [taskState, setTaskState] = useState<TaskState>('loading');
  const [submissionId, setSubmissionId] = useState<number | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answeredQuestions, setAnsweredQuestions] = useState<AnsweredQuestion[]>([]);
  const [completionResult, setCompletionResult] = useState<any>(null);

  // Refs
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const hasStartedRef = useRef(false);

  // Queries & Mutations
  const { data: homework } = useHomeworkDetail(homeworkId);
  const { data: questions, isLoading: questionsLoading } = useTaskQuestions(
    homeworkId,
    taskId
  );
  const startTaskMutation = useStartTask(homeworkId!);
  const submitAnswerMutation = useSubmitAnswer();
  const completeSubmissionMutation = useCompleteSubmission(homeworkId!);

  // Find current task
  const currentTask = homework?.tasks.find((t) => t.id === taskId);

  // Initialize task state
  useEffect(() => {
    if (!currentTask || hasStartedRef.current) return;

    if (currentTask.status === SubmissionStatus.NOT_STARTED) {
      setTaskState('not_started');
    } else if (currentTask.status === SubmissionStatus.IN_PROGRESS) {
      setSubmissionId(currentTask.submission_id || null);
      setTaskState('in_progress');
      // Set currentIndex based on answered_count
      setCurrentIndex(currentTask.answered_count);
    } else {
      setTaskState('completed');
    }
    hasStartedRef.current = true;
  }, [currentTask]);

  // Auto-scroll when new answer added
  useEffect(() => {
    if (scrollContainerRef.current && answeredQuestions.length > 0) {
      scrollContainerRef.current.scrollTo({
        top: scrollContainerRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [answeredQuestions]);

  // Handle start task
  const handleStartTask = useCallback(async () => {
    if (!taskId) return;

    try {
      const result = await startTaskMutation.mutateAsync(taskId);
      setSubmissionId(result.submission_id || result.id);
      setTaskState('in_progress');
    } catch (error) {
      console.error('Failed to start task:', error);
    }
  }, [taskId, startTaskMutation]);

  // Handle answer submission
  const handleAnswer = useCallback(
    async (
      question: StudentQuestionResponse,
      answerText?: string,
      selectedOptions?: string[]
    ): Promise<SubmissionResult> => {
      if (!submissionId) throw new Error('No submission ID');

      const result = await submitAnswerMutation.mutateAsync({
        submissionId,
        data: {
          question_id: question.id,
          answer_text: answerText,
          selected_options: selectedOptions,
        },
      });

      // Add to answered questions
      setAnsweredQuestions((prev) => [...prev, { question, feedback: result }]);

      // Move to next question
      if (questions && currentIndex < questions.length - 1) {
        setCurrentIndex((prev) => prev + 1);
      }

      return result;
    },
    [submissionId, submitAnswerMutation, questions, currentIndex]
  );

  // Handle complete submission
  const handleComplete = useCallback(async () => {
    if (!submissionId) return;

    try {
      const result = await completeSubmissionMutation.mutateAsync(submissionId);
      setCompletionResult(result);
      setTaskState('completed');
    } catch (error) {
      console.error('Failed to complete submission:', error);
    }
  }, [submissionId, completeSubmissionMutation]);

  // Navigate back
  const handleBackToHomework = () => {
    router.push(`/${locale}/homework/${homeworkId}`);
  };

  const handleTryAgain = () => {
    setTaskState('not_started');
    setCurrentIndex(0);
    setAnsweredQuestions([]);
    setCompletionResult(null);
    setSubmissionId(null);
    hasStartedRef.current = false;
  };

  // Render question based on type
  const renderQuestion = (question: StudentQuestionResponse, index: number) => {
    const isChoiceType = [
      QuestionType.SINGLE_CHOICE,
      QuestionType.MULTIPLE_CHOICE,
      QuestionType.TRUE_FALSE,
    ].includes(question.question_type);

    if (isChoiceType) {
      return (
        <ChoiceQuestion
          key={question.id}
          question={question}
          questionNumber={index + 1}
          onAnswer={async (selectedOptions) => {
            return handleAnswer(question, undefined, selectedOptions);
          }}
        />
      );
    }

    return (
      <TextQuestion
        key={question.id}
        question={question}
        questionNumber={index + 1}
        onAnswer={async (answerText) => {
          return handleAnswer(question, answerText, undefined);
        }}
      />
    );
  };

  // Loading state
  if (taskState === 'loading' || questionsLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 text-primary animate-spin mb-4" />
        <p className="text-gray-500">{t('loading')}</p>
      </div>
    );
  }

  // Completed state with results
  if (taskState === 'completed' && completionResult) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-6">
        <SubmissionResultCard
          result={completionResult}
          taskType={currentTask?.task_type}
          onBackToHomework={handleBackToHomework}
          onTryAgain={handleTryAgain}
          canTryAgain={(currentTask?.attempts_remaining ?? 0) > 0}
        />
      </div>
    );
  }

  // Not started state
  if (taskState === 'not_started') {
    return (
      <div className="mx-auto max-w-2xl px-4 py-6">
        {/* Back Button */}
        <Link
          href={`/homework/${homeworkId}`}
          className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          {t('result.backToHomework')}
        </Link>

        <div className="card-elevated p-6 text-center">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
            <CheckCircle2 className="w-8 h-8 text-primary" />
          </div>

          <h2 className="text-xl font-bold text-gray-900 mb-2">
            {currentTask?.paragraph_title || t('taskType.' + currentTask?.task_type)}
          </h2>

          {currentTask?.instructions && (
            <p className="text-gray-600 mb-4">{currentTask.instructions}</p>
          )}

          <div className="flex flex-wrap items-center justify-center gap-4 text-sm text-gray-500 mb-6">
            <span>{t('task.questions', { count: currentTask?.questions_count || 0 })}</span>
            <span>{t('task.points', { count: currentTask?.points || 0 })}</span>
            {currentTask?.time_limit_minutes && (
              <span className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {t('task.timeLimit', { minutes: currentTask.time_limit_minutes })}
              </span>
            )}
          </div>

          <button
            onClick={handleStartTask}
            disabled={startTaskMutation.isPending}
            className="px-8 py-3 rounded-xl font-medium bg-primary text-white hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {startTaskMutation.isPending ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              t('task.start')
            )}
          </button>

          {/* Attempts info */}
          <p className="text-sm text-gray-500 mt-4">
            {t('task.attempt', {
              current: (currentTask?.current_attempt || 0) + 1,
              max: currentTask?.max_attempts || 1,
            })}
          </p>
        </div>
      </div>
    );
  }

  // In progress state - Quiz UI
  const totalQuestions = questions?.length || 0;
  const allAnswered = answeredQuestions.length >= totalQuestions;

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="bg-white border-b px-4 py-3 shrink-0">
        <div className="mx-auto max-w-2xl flex items-center justify-between">
          <Link
            href={`/homework/${homeworkId}`}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="hidden sm:inline">{t('result.backToHomework')}</span>
          </Link>

          <div className="text-center">
            <p className="text-sm font-medium text-gray-900">
              {t('question.number', {
                current: Math.min(answeredQuestions.length + 1, totalQuestions),
                total: totalQuestions,
              })}
            </p>
          </div>

          <div className="w-16" /> {/* Spacer for centering */}
        </div>

        {/* Progress Bar */}
        <div className="mx-auto max-w-2xl mt-2">
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-500"
              style={{
                width: `${(answeredQuestions.length / totalQuestions) * 100}%`,
              }}
            />
          </div>
        </div>
      </div>

      {/* Content */}
      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto px-4 py-6"
      >
        <div className="mx-auto max-w-2xl space-y-6">
          {/* Answered Questions History */}
          {answeredQuestions.map((answered, idx) => (
            <div key={answered.question.id} className="space-y-3 opacity-60">
              {/* Question */}
              <div className="bg-gray-50 rounded-2xl p-4">
                <p className="text-sm text-primary font-medium mb-2">
                  {t('question.number', { current: idx + 1, total: totalQuestions })}
                </p>
                <p className="font-semibold text-gray-900">
                  {answered.question.question_text}
                </p>
              </div>

              {/* Feedback */}
              <QuestionFeedback
                feedback={answered.feedback}
                taskType={currentTask?.task_type}
                showExplanation={homework?.show_explanations}
              />
            </div>
          ))}

          {/* Current Question */}
          {!allAnswered && questions && questions[currentIndex] && (
            <div className="bg-white rounded-2xl border-2 border-primary/20 p-6">
              {renderQuestion(questions[currentIndex], currentIndex)}
            </div>
          )}

          {/* All Questions Answered - Complete Button */}
          {allAnswered && (
            <div className="text-center py-8">
              <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
                <CheckCircle2 className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">
                {t('allQuestionsAnswered')}
              </h3>
              <p className="text-gray-600 mb-6">{t('clickToComplete')}</p>
              <button
                onClick={handleComplete}
                disabled={completeSubmissionMutation.isPending}
                className="px-8 py-3 rounded-xl font-medium bg-primary text-white hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                {completeSubmissionMutation.isPending ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  t('question.finish')
                )}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
