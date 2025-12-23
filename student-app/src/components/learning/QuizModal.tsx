'use client';

import { useState, useEffect, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { cn } from '@/lib/utils';
import { AvailableTest, TestAttemptDetail, AnswerSubmit, QuestionOptionWithAnswer } from '@/lib/api/tests';
import { useStartTest, useSubmitTest } from '@/lib/hooks/use-tests';
import { QuizQuestion } from './QuizQuestion';
import { QuizResult } from './QuizResult';
import { X, Loader2, ChevronLeft, ChevronRight, Brain } from 'lucide-react';

interface QuizModalProps {
  isOpen: boolean;
  onClose: () => void;
  test: AvailableTest;
  paragraphId: number;
  onCompleted?: (passed: boolean, score: number) => void;
}

type QuizState = 'loading' | 'in_progress' | 'submitting' | 'completed';

export function QuizModal({
  isOpen,
  onClose,
  test,
  paragraphId,
  onCompleted,
}: QuizModalProps) {
  const t = useTranslations('paragraph.quiz');

  // State
  const [quizState, setQuizState] = useState<QuizState>('loading');
  const [attempt, setAttempt] = useState<TestAttemptDetail | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Map<number, number[]>>(new Map());

  // Mutations
  const startTestMutation = useStartTest();
  const submitTestMutation = useSubmitTest(paragraphId);

  // Start test when modal opens
  useEffect(() => {
    if (isOpen && !attempt) {
      startTestMutation.mutate(test.id, {
        onSuccess: (data) => {
          setAttempt(data);
          setQuizState('in_progress');
          setCurrentQuestionIndex(0);
          setAnswers(new Map());
        },
        onError: (error) => {
          console.error('Failed to start test:', error);
          onClose();
        },
      });
    }
  }, [isOpen, test.id, attempt, startTestMutation, onClose]);

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setAttempt(null);
      setQuizState('loading');
      setCurrentQuestionIndex(0);
      setAnswers(new Map());
    }
  }, [isOpen]);

  // Handle answer selection
  const handleAnswer = useCallback((optionIds: number[]) => {
    if (!attempt) return;
    const question = attempt.test.questions[currentQuestionIndex];
    setAnswers(prev => new Map(prev).set(question.id, optionIds));
  }, [attempt, currentQuestionIndex]);

  // Navigate questions
  const goToNextQuestion = useCallback(() => {
    if (!attempt) return;
    if (currentQuestionIndex < attempt.test.questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    }
  }, [attempt, currentQuestionIndex]);

  const goToPreviousQuestion = useCallback(() => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
    }
  }, [currentQuestionIndex]);

  // Submit test
  const handleSubmit = useCallback(() => {
    if (!attempt) return;

    // Convert answers map to AnswerSubmit array
    const answersList: AnswerSubmit[] = attempt.test.questions.map(q => ({
      question_id: q.id,
      selected_option_ids: answers.get(q.id) || [],
    }));

    setQuizState('submitting');

    submitTestMutation.mutate(
      { attemptId: attempt.id, answers: answersList },
      {
        onSuccess: (data) => {
          setAttempt(data);
          setQuizState('completed');
          onCompleted?.(data.passed ?? false, data.score ?? 0);
        },
        onError: (error) => {
          console.error('Failed to submit test:', error);
          setQuizState('in_progress');
        },
      }
    );
  }, [attempt, answers, submitTestMutation, onCompleted]);

  // Retake test
  const handleRetake = useCallback(() => {
    setAttempt(null);
    setQuizState('loading');
    setCurrentQuestionIndex(0);
    setAnswers(new Map());
    // This will trigger the useEffect to start a new test
  }, []);

  // Don't render if not open
  if (!isOpen) return null;

  const questions = attempt?.test.questions || [];
  const currentQuestion = questions[currentQuestionIndex];
  const totalQuestions = questions.length;
  const answeredCount = answers.size;
  const allAnswered = answeredCount === totalQuestions;
  const isLastQuestion = currentQuestionIndex === totalQuestions - 1;

  // Get correct option IDs for result display
  const getCorrectOptionIds = (questionId: number): number[] => {
    if (quizState !== 'completed' || !attempt) return [];
    const answer = attempt.answers.find(a => a.question_id === questionId);
    if (!answer) return [];
    // Find the question and get correct options
    const question = attempt.test.questions.find(q => q.id === questionId);
    if (!question) return [];
    // Options should have is_correct after submission
    return (question.options as QuestionOptionWithAnswer[])
      .filter(o => o.is_correct)
      .map(o => o.id);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-gray-50 rounded-2xl shadow-2xl mx-4">
        {/* Header */}
        <div className="sticky top-0 z-10 bg-white border-b px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center">
              <Brain className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <h2 className="font-bold text-gray-900">{t('title')}</h2>
              <p className="text-sm text-gray-500">{test.title}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center hover:bg-gray-200 transition-colors"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Loading State */}
          {quizState === 'loading' && (
            <div className="flex flex-col items-center justify-center py-20">
              <Loader2 className="w-10 h-10 text-amber-500 animate-spin mb-4" />
              <p className="text-gray-600">{t('loading')}</p>
            </div>
          )}

          {/* In Progress State */}
          {quizState === 'in_progress' && currentQuestion && (
            <>
              {/* Progress Bar */}
              <div className="mb-6">
                <div className="flex justify-between text-sm text-gray-600 mb-2">
                  <span>{t('progress', { answered: answeredCount, total: totalQuestions })}</span>
                  <span>{t('question', { current: currentQuestionIndex + 1, total: totalQuestions })}</span>
                </div>
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-amber-500 transition-all duration-300"
                    style={{ width: `${(answeredCount / totalQuestions) * 100}%` }}
                  />
                </div>
              </div>

              {/* Question */}
              <QuizQuestion
                question={currentQuestion}
                questionNumber={currentQuestionIndex + 1}
                totalQuestions={totalQuestions}
                selectedAnswer={answers.get(currentQuestion.id) || null}
                onAnswer={handleAnswer}
              />

              {/* Navigation */}
              <div className="flex items-center justify-between mt-6">
                <button
                  onClick={goToPreviousQuestion}
                  disabled={currentQuestionIndex === 0}
                  className={cn(
                    'flex items-center gap-2 px-4 py-2 rounded-xl font-medium transition-colors',
                    currentQuestionIndex === 0
                      ? 'text-gray-400 cursor-not-allowed'
                      : 'text-gray-700 hover:bg-gray-200'
                  )}
                >
                  <ChevronLeft className="w-5 h-5" />
                  {t('previous')}
                </button>

                <div className="flex gap-2">
                  {questions.map((q, index) => (
                    <button
                      key={q.id}
                      onClick={() => setCurrentQuestionIndex(index)}
                      className={cn(
                        'w-8 h-8 rounded-full text-sm font-medium transition-colors',
                        index === currentQuestionIndex
                          ? 'bg-amber-500 text-white'
                          : answers.has(q.id)
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                      )}
                    >
                      {index + 1}
                    </button>
                  ))}
                </div>

                {isLastQuestion ? (
                  <button
                    onClick={handleSubmit}
                    disabled={!allAnswered}
                    className={cn(
                      'flex items-center gap-2 px-6 py-2 rounded-xl font-medium transition-colors',
                      allAnswered
                        ? 'bg-green-500 text-white hover:bg-green-600'
                        : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                    )}
                  >
                    {t('submit')}
                  </button>
                ) : (
                  <button
                    onClick={goToNextQuestion}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl font-medium text-gray-700 hover:bg-gray-200 transition-colors"
                  >
                    {t('next')}
                    <ChevronRight className="w-5 h-5" />
                  </button>
                )}
              </div>
            </>
          )}

          {/* Submitting State */}
          {quizState === 'submitting' && (
            <div className="flex flex-col items-center justify-center py-20">
              <Loader2 className="w-10 h-10 text-amber-500 animate-spin mb-4" />
              <p className="text-gray-600">{t('submitting')}</p>
            </div>
          )}

          {/* Completed State */}
          {quizState === 'completed' && attempt && (
            <QuizResult
              attempt={attempt}
              onRetake={handleRetake}
              onClose={onClose}
            />
          )}
        </div>
      </div>
    </div>
  );
}
