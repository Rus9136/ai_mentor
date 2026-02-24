'use client';

import { use, useState, useMemo, useCallback, useRef, useEffect } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { Link, useRouter } from '@/i18n/routing';
import {
  useParagraphDetail,
  useParagraphRichContent,
  useParagraphNavigation,
  useParagraphProgress,
  useUpdateParagraphStep,
  useSubmitSelfAssessment,
  useEmbeddedQuestions,
  useAnswerEmbeddedQuestion,
  useChapterParagraphs,
} from '@/lib/hooks/use-textbooks';
import { useParagraphTest } from '@/lib/hooks/use-tests';
import { getMediaUrl } from '@/lib/api/client';
import { ParagraphStep, SelfAssessmentRating, AnswerResult } from '@/lib/api/textbooks';
import {
  EmbeddedQuestion,
  SelfAssessment,
  CompletionScreen,
  ParagraphQuiz,
  ChapterSidebar,
  MobileSidebarTrigger,
  MobileSidebarSheet,
} from '@/components/learning';
import { ChatModal } from '@/components/chat';
import { renderMathInHtml } from '@/components/common/MathText';
import {
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  Loader2,
  AlertCircle,
  BookOpen,
  Headphones,
  Layers,
  Target,
  Key,
  Volume2,
  Pause,
  Play,
  RotateCcw,
  Brain,
  Sparkles,
} from 'lucide-react';

// Content tabs
type ContentTab = 'text' | 'audio' | 'cards' | 'practice';

// Learning flow phases — state machine for paragraph completion
type LearningFlowPhase =
  | 'reading'        // Reading content (default)
  | 'questions'      // Embedded questions "Проверь себя"
  | 'assessment'     // First self-assessment
  | 'chat'           // AI chat (after "not understood")
  | 'reassessment'   // Repeat self-assessment after chat
  | 'completed';     // Paragraph completed

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function ParagraphPage({ params }: PageProps) {
  const { id } = use(params);
  const paragraphId = parseInt(id, 10);

  const t = useTranslations('paragraph');
  const tCommon = useTranslations('common');
  const tChat = useTranslations('chat');
  const router = useRouter();
  const locale = useLocale();

  // Active content tab
  const [activeTab, setActiveTab] = useState<ContentTab>('text');
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [showCompletion, setShowCompletion] = useState(false);
  const [showMobileSidebar, setShowMobileSidebar] = useState(false);
  const [showChat, setShowChat] = useState(false);

  // Learning flow state machine
  const [flowPhase, setFlowPhase] = useState<LearningFlowPhase>('reading');
  const [assessmentRound, setAssessmentRound] = useState(0);

  // Fetch paragraph data
  const { data: paragraph, isLoading, error } = useParagraphDetail(paragraphId);
  const { data: richContent } = useParagraphRichContent(paragraphId, locale as 'ru' | 'kz');
  const { data: navigation } = useParagraphNavigation(paragraphId);
  const { data: progress, refetch: refetchProgress } = useParagraphProgress(paragraphId);
  const { data: embeddedQuestions } = useEmbeddedQuestions(paragraphId);
  const { data: paragraphTest } = useParagraphTest(paragraph?.id);

  // Fetch all paragraphs in chapter for sidebar
  const { data: chapterParagraphs } = useChapterParagraphs(navigation?.chapter_id);

  // Mutations
  const updateStepMutation = useUpdateParagraphStep(paragraphId);
  const submitAssessmentMutation = useSubmitSelfAssessment(paragraphId);
  const answerQuestionMutation = useAnswerEmbeddedQuestion(paragraphId);

  // Time tracking: record when student opened the paragraph
  const lastSentRef = useRef<number>(Date.now());

  // Reset timer when paragraph changes
  useEffect(() => {
    lastSentRef.current = Date.now();
  }, [paragraphId]);

  // Get elapsed seconds since last send and reset timer (capped at 3600s per backend validation)
  const getAndResetElapsed = useCallback(() => {
    const now = Date.now();
    const elapsed = Math.min(Math.round((now - lastSentRef.current) / 1000), 3600);
    lastSentRef.current = now;
    return elapsed;
  }, []);

  // Handle step change
  const handleStepChange = useCallback(async (step: ParagraphStep) => {
    try {
      await updateStepMutation.mutateAsync({ step, timeSpent: getAndResetElapsed() });
      // Switch to appropriate tab based on step
      if (step === 'content') setActiveTab('text');
      if (step === 'practice') setActiveTab('practice');
    } catch (error) {
      console.error('Failed to update step:', error);
    }
  }, [updateStepMutation, getAndResetElapsed]);

  // Handle "Завершить изучение" button click — start the learning flow
  const handleFinishStudying = useCallback(async () => {
    const hasQuestions = embeddedQuestions && embeddedQuestions.length > 0;
    if (hasQuestions) {
      await updateStepMutation.mutateAsync({ step: 'practice', timeSpent: getAndResetElapsed() });
      setCurrentQuestionIndex(0);
      setFlowPhase('questions');
    } else {
      await updateStepMutation.mutateAsync({ step: 'summary', timeSpent: getAndResetElapsed() });
      setFlowPhase('assessment');
    }
  }, [embeddedQuestions, updateStepMutation, getAndResetElapsed]);

  // Handle self-assessment submission — branch by student's rating
  // practice_score & time_spent are sent for backend analytics (mastery_impact, teacher dashboard)
  const handleSelfAssessment = useCallback(async (rating: SelfAssessmentRating) => {
    // Calculate practice_score from embedded questions progress
    const practiceScore =
      progress && progress.embedded_questions_total > 0
        ? (progress.embedded_questions_correct / progress.embedded_questions_total) * 100
        : null;

    const timeSpent = progress?.time_spent ?? null;

    // Submit enriched assessment data
    await submitAssessmentMutation.mutateAsync({
      rating,
      practice_score: practiceScore,
      time_spent: timeSpent,
    });

    if (rating === 'understood') {
      // Mark completed and show completion screen
      await updateStepMutation.mutateAsync({ step: 'completed', timeSpent: getAndResetElapsed() });
      await refetchProgress();
      setFlowPhase('completed');
      setShowCompletion(true);
    } else {
      // "questions" or "difficult" → open AI chat
      setFlowPhase('chat');
      setShowChat(true);
    }
  }, [submitAssessmentMutation, updateStepMutation, refetchProgress, progress, getAndResetElapsed]);

  // Handle embedded question answer
  const handleAnswerQuestion = useCallback(async (questionId: number, answer: string | string[]): Promise<AnswerResult> => {
    const result = await answerQuestionMutation.mutateAsync({ questionId, answer });
    return result;
  }, [answerQuestionMutation]);

  // Handle chat close — transition to reassessment
  const handleChatClose = useCallback(() => {
    setShowChat(false);
    if (flowPhase === 'chat') {
      setAssessmentRound(prev => prev + 1);
      setFlowPhase('reassessment');
    }
  }, [flowPhase]);

  // Handle next question
  const handleNextQuestion = useCallback(async () => {
    if (embeddedQuestions && currentQuestionIndex < embeddedQuestions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    } else if (flowPhase === 'questions') {
      // All questions answered in flow mode → move to assessment
      await updateStepMutation.mutateAsync({ step: 'summary', timeSpent: getAndResetElapsed() });
      await refetchProgress();
      setFlowPhase('assessment');
    } else {
      // Legacy: all questions answered outside flow mode
      handleStepChange('summary');
    }
  }, [embeddedQuestions, currentQuestionIndex, flowPhase, updateStepMutation, refetchProgress, handleStepChange, getAndResetElapsed]);

  // Determine available tabs
  const availableTabs = useMemo(() => {
    const tabs: ContentTab[] = ['text'];
    if (richContent?.has_audio || paragraph?.has_audio) tabs.push('audio');
    if (richContent?.has_cards || paragraph?.has_cards) tabs.push('cards');
    if (embeddedQuestions && embeddedQuestions.length > 0) tabs.push('practice');
    return tabs;
  }, [richContent, paragraph, embeddedQuestions]);

  // Get content to display (prefer rich content explain_text, fallback to paragraph content)
  // Process LaTeX formulas ($...$, $$...$$) via KaTeX
  const displayContent = useMemo(() => {
    const raw = richContent?.explain_text || paragraph?.content || null;
    if (!raw) return null;
    return renderMathInHtml(raw);
  }, [richContent, paragraph]);

  // Calculate completed count for mobile trigger (must be before conditional returns!)
  const completedCount = useMemo(() => {
    return chapterParagraphs?.filter((p) => p.status === 'completed').length || 0;
  }, [chapterParagraphs]);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <span className="ml-2 text-muted-foreground">{tCommon('loading')}</span>
      </div>
    );
  }

  // Error state
  if (error || !paragraph) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-12 text-center">
        <AlertCircle className="mx-auto h-12 w-12 text-destructive" />
        <h2 className="mt-4 text-lg font-bold">{tCommon('error')}</h2>
        <p className="mt-2 text-sm text-muted-foreground">{t('errorLoading')}</p>
        <button
          onClick={() => router.back()}
          className="mt-6 rounded-full bg-primary px-6 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
        >
          {tCommon('back')}
        </button>
      </div>
    );
  }

  return (
    <div className="flex min-h-[calc(100vh-4rem)]">
      {/* Desktop Sidebar */}
      {chapterParagraphs && navigation && (
        <ChapterSidebar
          paragraphs={chapterParagraphs}
          currentParagraphId={paragraphId}
          chapterTitle={navigation.chapter_title}
          chapterNumber={navigation.chapter_number}
          chapterId={navigation.chapter_id}
        />
      )}

      {/* Mobile Sidebar Sheet */}
      {chapterParagraphs && navigation && (
        <MobileSidebarSheet
          isOpen={showMobileSidebar}
          onClose={() => setShowMobileSidebar(false)}
          paragraphs={chapterParagraphs}
          currentParagraphId={paragraphId}
          chapterTitle={navigation.chapter_title}
          chapterNumber={navigation.chapter_number}
          chapterId={navigation.chapter_id}
        />
      )}

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-4xl px-4 py-6 pb-24 md:pb-8">
          {/* Header */}
          <header className="mb-6">
            {/* Top row: Back button + Mobile sidebar trigger */}
            <div className="mb-4 flex items-center justify-between">
              <Link
                href={navigation ? `/chapters/${navigation.chapter_id}` : '/subjects'}
                className="flex items-center gap-1 text-sm font-medium text-muted-foreground hover:text-foreground"
              >
                <ArrowLeft className="h-4 w-4" />
                {tCommon('back')}
              </Link>

              {/* Mobile sidebar trigger */}
              {chapterParagraphs && (
                <MobileSidebarTrigger
                  onClick={() => setShowMobileSidebar(true)}
                  paragraphsCount={chapterParagraphs.length}
                  completedCount={completedCount}
                />
              )}
            </div>

            {/* Breadcrumb */}
            {navigation && (
              <nav className="mb-2 flex items-center gap-2 text-sm text-muted-foreground">
                <Link
                  href={`/subjects/${navigation.textbook_id}`}
                  className="hover:text-primary truncate max-w-[120px] md:max-w-none"
                >
                  {navigation.textbook_title}
                </Link>
                <ChevronRight className="h-3 w-3 flex-shrink-0" />
                <Link
                  href={`/chapters/${navigation.chapter_id}`}
                  className="hover:text-primary truncate max-w-[100px] md:max-w-none"
                >
                  {t('chapterShort', { number: navigation.chapter_number })}
                </Link>
                <ChevronRight className="h-3 w-3 flex-shrink-0" />
                <span className="text-foreground font-medium">
                  §{navigation.current_paragraph_number}
                </span>
              </nav>
            )}

            {/* Title */}
            <h1 className="text-2xl font-bold text-foreground md:text-3xl">
              §{paragraph.number}. {paragraph.title || t('untitled')}
            </h1>

            {/* Progress indicator - hide on desktop when sidebar is visible */}
            {navigation && (
              <div className="mt-4 card-flat p-3 lg:hidden">
                <div className="flex items-center justify-between text-sm mb-2">
                  <span className="text-muted-foreground">{t('progressInChapter')}</span>
                  <span className="font-medium">
                    {navigation.current_position_in_chapter} {t('of')}{' '}
                    {navigation.total_paragraphs_in_chapter}
                  </span>
                </div>
                <div className="flex gap-1">
                  {Array.from({ length: navigation.total_paragraphs_in_chapter }).map((_, i) => (
                    <div
                      key={i}
                      className={`h-2 flex-1 rounded-full transition-all ${
                        i + 1 < navigation.current_position_in_chapter
                          ? 'bg-success'
                          : i + 1 === navigation.current_position_in_chapter
                          ? 'bg-primary'
                          : 'bg-muted'
                      }`}
                    />
                  ))}
                </div>
              </div>
            )}

      </header>

      {/* Learning Objective */}
      {paragraph.learning_objective && (
        <section className="mb-6 card-flat border-l-4 border-l-primary p-4">
          <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-primary/10">
              <Target className="h-4 w-4 text-primary" />
            </div>
            <div>
              <h2 className="font-semibold text-foreground mb-1">{t('learningObjective')}</h2>
              <p className="text-sm text-muted-foreground">{paragraph.learning_objective}</p>
            </div>
          </div>
        </section>
      )}

      {/* Key Terms */}
      {paragraph.key_terms && paragraph.key_terms.length > 0 && (
        <section className="mb-6">
          <div className="flex items-center gap-2 mb-3">
            <Key className="h-4 w-4 text-primary" />
            <h2 className="font-semibold text-foreground">{t('keyTerms')}</h2>
          </div>
          <div className="flex flex-wrap gap-2">
            {paragraph.key_terms.map((term, index) => (
              <span
                key={index}
                className="rounded-full bg-primary/10 px-3 py-1 text-sm font-medium text-primary"
              >
                {term}
              </span>
            ))}
          </div>
        </section>
      )}

      {/* === PHASE: READING — Content tabs and material === */}
      {flowPhase === 'reading' && (
        <>
          {/* Content Tabs */}
          {availableTabs.length > 1 && (
            <div className="mb-4 flex gap-2 overflow-x-auto pb-2">
              {availableTabs.map((tab) => {
                const TabIcon = tab === 'text' ? BookOpen : tab === 'audio' ? Headphones : tab === 'practice' ? Brain : Layers;
                const tabLabel = tab === 'practice' ? t('steps.practice') : t(`tabs.${tab}`);
                return (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-all ${
                      activeTab === tab
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted text-muted-foreground hover:bg-muted/80'
                    }`}
                  >
                    <TabIcon className="h-4 w-4" />
                    {tabLabel}
                    {tab === 'practice' && progress && progress.embedded_questions_total > 0 && (
                      <span className="ml-1 px-1.5 py-0.5 text-xs rounded-full bg-white/20">
                        {progress.embedded_questions_answered}/{progress.embedded_questions_total}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          )}

          {/* Content Area */}
          <main className="mb-8">
            {/* Text Content */}
            {activeTab === 'text' && (
              <article className="card-elevated p-6">
                {displayContent ? (
                  <div
                    className="prose prose-stone dark:prose-invert max-w-none
                      prose-headings:text-foreground prose-headings:font-bold
                      prose-p:text-foreground prose-p:leading-relaxed
                      prose-strong:text-foreground prose-strong:font-semibold
                      prose-ul:text-foreground prose-ol:text-foreground
                      prose-li:marker:text-primary"
                    dangerouslySetInnerHTML={{ __html: displayContent }}
                  />
                ) : (
                  <div className="text-center py-8">
                    <BookOpen className="mx-auto h-12 w-12 text-muted-foreground/50" />
                    <p className="mt-4 text-muted-foreground">{t('noContent')}</p>
                  </div>
                )}
              </article>
            )}

            {/* Audio Content */}
            {activeTab === 'audio' && (
              <AudioPlayer audioUrl={getMediaUrl(richContent?.audio_url)} t={t} />
            )}

            {/* Cards Content */}
            {activeTab === 'cards' && (
              <FlashCards cards={richContent?.cards || []} t={t} />
            )}

            {/* Practice Content - Embedded Questions (tab mode, for already completed paragraphs) */}
            {activeTab === 'practice' && embeddedQuestions && embeddedQuestions.length > 0 && (
              <div className="space-y-6">
                <div className="text-center mb-6">
                  <h2 className="text-xl font-bold text-foreground mb-2">{t('practice.title')}</h2>
                  <p className="text-muted-foreground">{t('practice.subtitle')}</p>
                  {progress && progress.embedded_questions_answered === progress.embedded_questions_total && progress.embedded_questions_total > 0 && (
                    <div className="mt-4 inline-flex items-center gap-2 bg-success/10 text-success px-4 py-2 rounded-full">
                      <span className="font-medium">{t('practice.completed')}</span>
                      <span className="text-sm">
                        {t('practice.score', {
                          correct: progress.embedded_questions_correct,
                          total: progress.embedded_questions_total
                        })}
                      </span>
                    </div>
                  )}
                </div>

                <EmbeddedQuestion
                  question={embeddedQuestions[currentQuestionIndex]}
                  questionNumber={currentQuestionIndex + 1}
                  totalQuestions={embeddedQuestions.length}
                  onAnswer={handleAnswerQuestion}
                  onNext={handleNextQuestion}
                  isLast={currentQuestionIndex === embeddedQuestions.length - 1}
                />

                {embeddedQuestions.length > 1 && (
                  <div className="flex justify-center gap-2">
                    {embeddedQuestions.map((_, index) => (
                      <button
                        key={index}
                        onClick={() => setCurrentQuestionIndex(index)}
                        className={`w-3 h-3 rounded-full transition-all ${
                          index === currentQuestionIndex
                            ? 'bg-primary scale-125'
                            : 'bg-muted hover:bg-muted/80'
                        }`}
                      />
                    ))}
                  </div>
                )}
              </div>
            )}
          </main>

          {/* Paragraph Quiz - Chat-like quiz under content */}
          {paragraphTest && paragraph && (
            <section className="mb-8">
              <ParagraphQuiz
                test={paragraphTest}
                paragraphId={paragraph.id}
                onComplete={(passed, score) => {
                  refetchProgress();
                  console.log(`Quiz completed: passed=${passed}, score=${score}`);
                }}
              />
            </section>
          )}
        </>
      )}

      {/* === PHASE: QUESTIONS — Embedded questions in focus mode === */}
      {flowPhase === 'questions' && embeddedQuestions && embeddedQuestions.length > 0 && (
        <section className="mb-8">
          <div className="space-y-6">
            <div className="text-center mb-6">
              <h2 className="text-xl font-bold text-foreground mb-2">{t('practice.title')}</h2>
              <p className="text-muted-foreground">{t('practice.subtitle')}</p>
              {progress && progress.embedded_questions_answered === progress.embedded_questions_total && progress.embedded_questions_total > 0 && (
                <div className="mt-4 inline-flex items-center gap-2 bg-success/10 text-success px-4 py-2 rounded-full">
                  <span className="font-medium">{t('practice.completed')}</span>
                  <span className="text-sm">
                    {t('practice.score', {
                      correct: progress.embedded_questions_correct,
                      total: progress.embedded_questions_total
                    })}
                  </span>
                </div>
              )}
            </div>

            <EmbeddedQuestion
              question={embeddedQuestions[currentQuestionIndex]}
              questionNumber={currentQuestionIndex + 1}
              totalQuestions={embeddedQuestions.length}
              onAnswer={handleAnswerQuestion}
              onNext={handleNextQuestion}
              isLast={currentQuestionIndex === embeddedQuestions.length - 1}
            />

            {embeddedQuestions.length > 1 && (
              <div className="flex justify-center gap-2">
                {embeddedQuestions.map((_, index) => (
                  <button
                    key={index}
                    onClick={() => setCurrentQuestionIndex(index)}
                    className={`w-3 h-3 rounded-full transition-all ${
                      index === currentQuestionIndex
                        ? 'bg-primary scale-125'
                        : 'bg-muted hover:bg-muted/80'
                    }`}
                  />
                ))}
              </div>
            )}
          </div>
        </section>
      )}

      {/* === PHASE: ASSESSMENT / REASSESSMENT — Self-assessment buttons === */}
      {(flowPhase === 'assessment' || flowPhase === 'reassessment') && (
        <section className="mb-8">
          <SelfAssessment
            key={`assessment-${assessmentRound}`}
            onSubmit={handleSelfAssessment}
          />
        </section>
      )}

      {/* === PHASE: COMPLETED — Completion screen === */}
      {showCompletion && progress && navigation && paragraph && (
        <CompletionScreen
          paragraphTitle={paragraph.title}
          paragraphNumber={paragraph.number}
          questionsTotal={progress.embedded_questions_total}
          questionsCorrect={progress.embedded_questions_correct}
          timeSpentSeconds={progress.time_spent || 0}
          selfAssessment={progress.self_assessment}
          nextParagraphId={navigation.next_paragraph_id}
          chapterId={navigation.chapter_id}
          chapterTitle={navigation.chapter_title}
          isLastInChapter={!navigation.next_paragraph_id}
          onGoToNext={() => {
            if (navigation.next_paragraph_id) {
              router.push(`/paragraphs/${navigation.next_paragraph_id}`);
            }
          }}
          onGoToChapter={() => {
            router.push(`/chapters/${navigation.chapter_id}`);
          }}
        />
      )}

      {/* === NAVIGATION BAR === */}
      {!showCompletion && flowPhase !== 'questions' && flowPhase !== 'assessment' && flowPhase !== 'reassessment' && (
        <nav className="fixed bottom-0 left-0 right-0 bg-background/95 backdrop-blur border-t p-4 md:static md:border-0 md:bg-transparent md:p-0">
          <div className="mx-auto max-w-4xl flex items-center justify-between gap-4">
            {/* Previous */}
            {navigation?.previous_paragraph_id ? (
              <Link
                href={`/paragraphs/${navigation.previous_paragraph_id}`}
                className="flex items-center gap-2 rounded-full bg-muted px-4 py-2 text-sm font-medium text-muted-foreground hover:bg-muted/80 hover:text-foreground transition-all"
              >
                <ChevronLeft className="h-4 w-4" />
                <span className="hidden sm:inline">{t('previous')}</span>
              </Link>
            ) : (
              <div />
            )}

            {/* Center section: Chapter link */}
            {navigation && (
              <Link
                href={`/chapters/${navigation.chapter_id}`}
                className="text-sm text-muted-foreground hover:text-primary"
              >
                {t('backToChapter')}
              </Link>
            )}

            {/* Right button: "Завершить изучение" for incomplete, "Далее" for completed */}
            {progress?.is_completed ? (
              // Already completed — normal navigation
              navigation?.next_paragraph_id ? (
                <Link
                  href={`/paragraphs/${navigation.next_paragraph_id}`}
                  className="flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 transition-all"
                >
                  <span className="hidden sm:inline">{tCommon('next')}</span>
                  <ChevronRight className="h-4 w-4" />
                </Link>
              ) : (
                <Link
                  href={`/chapters/${navigation?.chapter_id || ''}`}
                  className="flex items-center gap-2 rounded-full bg-success px-4 py-2 text-sm font-medium text-white hover:opacity-90 transition-all"
                >
                  <span>{t('finishChapter')}</span>
                </Link>
              )
            ) : (
              // Not completed — "Завершить изучение" button
              <button
                onClick={handleFinishStudying}
                disabled={updateStepMutation.isPending}
                className="flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 transition-all disabled:opacity-50"
              >
                <span>{t('finishStudying')}</span>
                <ChevronRight className="h-4 w-4" />
              </button>
            )}
          </div>
        </nav>
      )}

        </div>
      </div>

      {/* Floating AI Chat Button — hide during chat flow phase */}
      {flowPhase !== 'chat' && !showCompletion && (
        <button
          onClick={() => setShowChat(true)}
          className="fixed bottom-20 right-4 md:bottom-6 md:right-6 z-40 flex items-center gap-2 px-4 py-3 bg-success text-white rounded-full shadow-lg hover:bg-success/90 hover:shadow-xl transition-all"
        >
          <Sparkles className="w-5 h-5" />
          <span className="font-medium">{tChat('floatingButton')}</span>
        </button>
      )}

      {/* AI Chat Modal — uses post_paragraph during flow, reading_help otherwise */}
      <ChatModal
        isOpen={showChat}
        onClose={flowPhase === 'chat' ? handleChatClose : () => setShowChat(false)}
        sessionType={flowPhase === 'chat' ? 'post_paragraph' : 'reading_help'}
        paragraphId={paragraphId}
        chapterId={navigation?.chapter_id}
      />
    </div>
  );
}

// =============================================================================
// Audio Player Component
// =============================================================================

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type TranslateFunction = (key: string, values?: Record<string, any>) => string;

interface AudioPlayerProps {
  audioUrl: string | null | undefined;
  t: TranslateFunction;
}

function AudioPlayer({ audioUrl, t }: AudioPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  const formatTime = (time: number) => {
    const mins = Math.floor(time / 60);
    const secs = Math.floor(time % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (!audioUrl) {
    return (
      <div className="card-elevated p-8 text-center">
        <Headphones className="mx-auto h-12 w-12 text-muted-foreground/50" />
        <p className="mt-4 text-muted-foreground">{t('noAudio')}</p>
      </div>
    );
  }

  return (
    <div className="card-elevated p-6">
      <div className="flex flex-col items-center">
        {/* Album art placeholder */}
        <div className="w-32 h-32 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mb-6">
          <Volume2 className="h-12 w-12 text-primary" />
        </div>

        {/* Audio element */}
        <audio
          src={audioUrl}
          onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
          onLoadedMetadata={(e) => setDuration(e.currentTarget.duration)}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          onEnded={() => setIsPlaying(false)}
          id="audio-player"
          className="hidden"
        />

        {/* Progress bar */}
        <div className="w-full max-w-md mb-4">
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-primary transition-all"
              style={{ width: `${duration ? (currentTime / duration) * 100 : 0}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-muted-foreground mt-1">
            <span>{formatTime(currentTime)}</span>
            <span>{formatTime(duration)}</span>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-4">
          <button
            onClick={() => {
              const audio = document.getElementById('audio-player') as HTMLAudioElement;
              if (audio) {
                audio.currentTime = 0;
              }
            }}
            className="p-3 rounded-full bg-muted hover:bg-muted/80 transition-all"
          >
            <RotateCcw className="h-5 w-5 text-muted-foreground" />
          </button>

          <button
            onClick={() => {
              const audio = document.getElementById('audio-player') as HTMLAudioElement;
              if (audio) {
                if (isPlaying) {
                  audio.pause();
                } else {
                  audio.play();
                }
              }
            }}
            className="p-4 rounded-full bg-primary text-primary-foreground hover:opacity-90 transition-all"
          >
            {isPlaying ? <Pause className="h-6 w-6" /> : <Play className="h-6 w-6 ml-0.5" />}
          </button>

          <div className="w-12" /> {/* Spacer for balance */}
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Flash Cards Component
// =============================================================================

interface FlashCard {
  id: string;
  type: string;
  front: string;
  back: string;
  order: number;
}

interface FlashCardsProps {
  cards: FlashCard[];
  t: TranslateFunction;
}

function FlashCards({ cards, t }: FlashCardsProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);

  if (!cards || cards.length === 0) {
    return (
      <div className="card-elevated p-8 text-center">
        <Layers className="mx-auto h-12 w-12 text-muted-foreground/50" />
        <p className="mt-4 text-muted-foreground">{t('noCards')}</p>
      </div>
    );
  }

  const currentCard = cards[currentIndex];

  const goNext = () => {
    if (currentIndex < cards.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setIsFlipped(false);
    }
  };

  const goPrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
      setIsFlipped(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Progress */}
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>
          {t('cardProgress', { current: currentIndex + 1, total: cards.length })}
        </span>
        <span>{t('tapToFlip')}</span>
      </div>

      {/* Card */}
      <div
        onClick={() => setIsFlipped(!isFlipped)}
        className="card-elevated cursor-pointer min-h-[250px] flex items-center justify-center p-8 transition-all hover:shadow-soft-lg"
        style={{ perspective: '1000px' }}
      >
        <div
          className={`w-full text-center transition-transform duration-500 ${
            isFlipped ? 'scale-y-[-1]' : ''
          }`}
          style={{ transformStyle: 'preserve-3d' }}
        >
          <div className={isFlipped ? 'scale-y-[-1]' : ''}>
            {!isFlipped ? (
              <div>
                <p className="text-xs text-muted-foreground mb-2">{t('cardFront')}</p>
                <p className="text-xl font-semibold text-foreground">{currentCard.front}</p>
              </div>
            ) : (
              <div>
                <p className="text-xs text-muted-foreground mb-2">{t('cardBack')}</p>
                <p className="text-lg text-foreground">{currentCard.back}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={goPrev}
          disabled={currentIndex === 0}
          className="flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium bg-muted text-muted-foreground hover:bg-muted/80 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          <ChevronLeft className="h-4 w-4" />
          {t('previousCard')}
        </button>

        <div className="flex gap-1">
          {cards.map((_, i) => (
            <button
              key={i}
              onClick={() => {
                setCurrentIndex(i);
                setIsFlipped(false);
              }}
              className={`h-2 w-2 rounded-full transition-all ${
                i === currentIndex ? 'bg-primary w-4' : 'bg-muted hover:bg-muted/80'
              }`}
            />
          ))}
        </div>

        <button
          onClick={goNext}
          disabled={currentIndex === cards.length - 1}
          className="flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium bg-primary text-primary-foreground hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          {t('nextCard')}
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
