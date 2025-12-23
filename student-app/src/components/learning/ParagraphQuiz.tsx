'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { cn } from '@/lib/utils';
import {
  AvailableTest,
  TestAttemptDetail,
  TestQuestion,
  QuestionOption,
} from '@/lib/api/tests';
import { useStartTest, useAnswerTestQuestion } from '@/lib/hooks/use-tests';
import { Loader2, Brain, CheckCircle2, XCircle, SkipForward } from 'lucide-react';

interface ParagraphQuizProps {
  test: AvailableTest;
  paragraphId: number;
  onComplete?: (passed: boolean, score: number) => void;
  onSkip?: () => void;
}

interface AnsweredQuestion {
  question: TestQuestion;
  selectedOptionIds: number[];
  isCorrect: boolean;
  correctOptionIds: number[];
  explanation: string | null;
  pointsEarned: number;
}

type QuizState = 'loading' | 'in_progress' | 'completed' | 'skipped';

export function ParagraphQuiz({
  test,
  paragraphId,
  onComplete,
  onSkip,
}: ParagraphQuizProps) {
  const t = useTranslations('paragraph.quiz');

  // State
  const [quizState, setQuizState] = useState<QuizState>('loading');
  const [attempt, setAttempt] = useState<TestAttemptDetail | null>(null);
  const [answeredQuestions, setAnsweredQuestions] = useState<AnsweredQuestion[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isAnswering, setIsAnswering] = useState(false);

  // Refs for auto-scroll
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const currentQuestionRef = useRef<HTMLDivElement>(null);

  // Mutations
  const startTestMutation = useStartTest();
  const answerMutation = useAnswerTestQuestion(paragraphId);

  // Start test on mount - use ref to prevent multiple calls
  const hasStartedRef = useRef(false);

  useEffect(() => {
    if (!hasStartedRef.current && quizState === 'loading') {
      hasStartedRef.current = true;
      startTestMutation.mutate(test.id, {
        onSuccess: (data) => {
          setAttempt(data);
          setQuizState('in_progress');
        },
        onError: (error) => {
          console.error('Failed to start test:', error);
          setQuizState('skipped');
        },
      });
    }
  }, [test.id, quizState, startTestMutation]);

  // Auto-scroll to current question when answered questions change
  useEffect(() => {
    if (scrollContainerRef.current && answeredQuestions.length > 0) {
      // Smooth scroll to bottom
      scrollContainerRef.current.scrollTo({
        top: scrollContainerRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [answeredQuestions]);

  // Handle option click - immediate answer
  const handleOptionClick = useCallback(
    async (optionId: number) => {
      if (!attempt || isAnswering || quizState !== 'in_progress') return;

      const currentQuestion = attempt.test.questions[currentIndex];
      if (!currentQuestion) return;

      setIsAnswering(true);

      try {
        const result = await answerMutation.mutateAsync({
          attemptId: attempt.id,
          questionId: currentQuestion.id,
          selectedOptionIds: [optionId],
        });

        // Add to answered questions
        const answered: AnsweredQuestion = {
          question: currentQuestion,
          selectedOptionIds: [optionId],
          isCorrect: result.is_correct,
          correctOptionIds: result.correct_option_ids,
          explanation: result.explanation,
          pointsEarned: result.points_earned,
        };

        setAnsweredQuestions((prev) => [...prev, answered]);

        // Check if test was auto-completed by the backend
        if (result.is_test_complete) {
          // Test is complete - backend already graded and updated mastery
          setQuizState('completed');
          onComplete?.(
            result.test_passed ?? false,
            result.test_score ?? 0
          );
        } else if (currentIndex < attempt.test.questions.length - 1) {
          // Move to next question
          setCurrentIndex((prev) => prev + 1);
        }
      } catch (error) {
        console.error('Failed to answer question:', error);
      } finally {
        setIsAnswering(false);
      }
    },
    [
      attempt,
      currentIndex,
      isAnswering,
      quizState,
      answerMutation,
      onComplete,
    ]
  );

  // Handle skip
  const handleSkip = useCallback(() => {
    setQuizState('skipped');
    onSkip?.();
  }, [onSkip]);

  // Calculate stats
  const totalQuestions = attempt?.test.questions.length || 0;
  const correctCount = answeredQuestions.filter((a) => a.isCorrect).length;
  const score =
    answeredQuestions.length > 0
      ? correctCount / answeredQuestions.length
      : 0;

  // Get option letter (A, B, C, D...)
  const getOptionLetter = (index: number) => String.fromCharCode(65 + index);

  // Don't render if skipped
  if (quizState === 'skipped') {
    return null;
  }

  return (
    <div className="card-elevated overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-amber-50 to-orange-50 border-b px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center">
            <Brain className="w-5 h-5 text-amber-600" />
          </div>
          <div className="flex-1">
            <h3 className="font-bold text-gray-900">{t('title')}</h3>
            {quizState === 'in_progress' && (
              <p className="text-sm text-gray-500">
                {t('progress', {
                  current: answeredQuestions.length + 1,
                  total: totalQuestions,
                })}
              </p>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        {quizState === 'in_progress' && totalQuestions > 0 && (
          <div className="mt-4">
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-amber-500 transition-all duration-500"
                style={{
                  width: `${(answeredQuestions.length / totalQuestions) * 100}%`,
                }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Content */}
      <div
        ref={scrollContainerRef}
        className="p-6 max-h-[600px] overflow-y-auto"
      >
        {/* Loading State */}
        {quizState === 'loading' && (
          <div className="flex flex-col items-center justify-center py-12">
            <Loader2 className="w-8 h-8 text-amber-500 animate-spin mb-4" />
            <p className="text-gray-600">{t('loading')}</p>
          </div>
        )}

        {/* Chat History - Answered Questions */}
        {(quizState === 'in_progress' || quizState === 'completed') && (
          <div className="space-y-6">
            {answeredQuestions.map((answered, idx) => (
              <div key={answered.question.id} className="space-y-3">
                {/* Question */}
                <div className="bg-gray-50 rounded-2xl p-4">
                  <p className="text-sm text-amber-600 font-medium mb-2">
                    {t('questionNumber', { number: idx + 1 })}
                  </p>
                  <p className="font-semibold text-gray-900">
                    {answered.question.question_text}
                  </p>
                </div>

                {/* User Answer Bubble - right aligned */}
                <div className="flex justify-end">
                  <div
                    className={cn(
                      'rounded-2xl px-4 py-2 max-w-[80%]',
                      answered.isCorrect
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    )}
                  >
                    {(() => {
                      const selectedOption = answered.question.options.find(
                        (o) => o.id === answered.selectedOptionIds[0]
                      );
                      const optionIndex = answered.question.options.findIndex(
                        (o) => o.id === answered.selectedOptionIds[0]
                      );
                      return selectedOption
                        ? `${getOptionLetter(optionIndex)}. ${selectedOption.option_text}`
                        : '';
                    })()}
                  </div>
                </div>

                {/* Feedback */}
                <div
                  className={cn(
                    'rounded-xl p-4 border',
                    answered.isCorrect
                      ? 'bg-green-50 border-green-200'
                      : 'bg-red-50 border-red-200'
                  )}
                >
                  <div className="flex items-center gap-2 mb-2">
                    {answered.isCorrect ? (
                      <>
                        <CheckCircle2 className="w-5 h-5 text-green-600" />
                        <span className="font-semibold text-green-700">
                          {t('correct')}
                        </span>
                      </>
                    ) : (
                      <>
                        <XCircle className="w-5 h-5 text-red-600" />
                        <span className="font-semibold text-red-700">
                          {t('incorrect')}
                        </span>
                      </>
                    )}
                  </div>

                  {/* Show correct answer if wrong */}
                  {!answered.isCorrect && (
                    <p className="text-sm text-gray-700 mb-2">
                      {t('correctAnswer')}:{' '}
                      <span className="font-medium">
                        {answered.correctOptionIds
                          .map((id) => {
                            const opt = answered.question.options.find(
                              (o) => o.id === id
                            );
                            const idx = answered.question.options.findIndex(
                              (o) => o.id === id
                            );
                            return opt
                              ? `${getOptionLetter(idx)}. ${opt.option_text}`
                              : '';
                          })
                          .join(', ')}
                      </span>
                    </p>
                  )}

                  {/* Explanation */}
                  {answered.explanation && (
                    <p className="text-sm text-gray-700">{answered.explanation}</p>
                  )}
                </div>
              </div>
            ))}

            {/* Current Question */}
            {quizState === 'in_progress' && attempt && currentIndex < totalQuestions && (
              <div ref={currentQuestionRef} className="space-y-4">
                <div className="bg-white rounded-2xl border-2 border-amber-200 p-6">
                  <p className="text-sm text-amber-600 font-medium mb-3">
                    {t('questionNumber', { number: currentIndex + 1 })}
                  </p>
                  <p className="text-lg font-semibold text-gray-900 mb-6">
                    {attempt.test.questions[currentIndex].question_text}
                  </p>

                  {/* Options */}
                  <div className="space-y-3">
                    {attempt.test.questions[currentIndex].options.map(
                      (option, optIdx) => (
                        <button
                          key={option.id}
                          onClick={() => handleOptionClick(option.id)}
                          disabled={isAnswering}
                          className={cn(
                            'w-full p-4 rounded-xl border-2 text-left flex items-center gap-3 transition-all',
                            isAnswering
                              ? 'opacity-50 cursor-not-allowed border-gray-200'
                              : 'border-gray-200 hover:border-amber-400 hover:bg-amber-50/50 cursor-pointer'
                          )}
                        >
                          <span className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center font-semibold text-gray-600">
                            {getOptionLetter(optIdx)}
                          </span>
                          <span className="flex-1">{option.option_text}</span>
                        </button>
                      )
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Completed State */}
            {quizState === 'completed' && (
              <div className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-2xl p-6 text-center">
                <div className="w-16 h-16 rounded-full bg-amber-100 flex items-center justify-center mx-auto mb-4">
                  <Brain className="w-8 h-8 text-amber-600" />
                </div>
                <h4 className="text-xl font-bold text-gray-900 mb-2">
                  {t('result.title')}
                </h4>
                <p className="text-gray-600 mb-4">
                  {t('result.score', {
                    correct: correctCount,
                    total: totalQuestions,
                  })}
                </p>
                <div
                  className={cn(
                    'inline-flex items-center gap-2 px-4 py-2 rounded-full font-medium',
                    score >= test.passing_score
                      ? 'bg-green-100 text-green-700'
                      : 'bg-red-100 text-red-700'
                  )}
                >
                  {score >= test.passing_score ? (
                    <>
                      <CheckCircle2 className="w-5 h-5" />
                      {t('result.passed')}
                    </>
                  ) : (
                    <>
                      <XCircle className="w-5 h-5" />
                      {t('result.failed')}
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      {quizState === 'in_progress' && (
        <div className="border-t px-6 py-4 flex justify-end">
          <button
            onClick={handleSkip}
            className="flex items-center gap-2 px-4 py-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-xl transition-colors"
          >
            <SkipForward className="w-4 h-4" />
            {t('skip')}
          </button>
        </div>
      )}
    </div>
  );
}
