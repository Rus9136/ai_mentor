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
  useExercises,
} from '@/lib/hooks/use-textbooks';
import { useParagraphTest } from '@/lib/hooks/use-tests';
import { getMediaUrl } from '@/lib/api/client';
import { ParagraphStep, SelfAssessmentRating, AnswerResult } from '@/lib/api/textbooks';
import {
  EmbeddedQuestion,
  SelfAssessment,
  CompletionScreen,
  ParagraphQuiz,
  MobileSidebarTrigger,
  MobileSidebarSheet,
  PrerequisiteWarning,
} from '@/components/learning';
import { usePrerequisiteCheck } from '@/lib/hooks/use-prerequisites';
import { ChatModal } from '@/components/chat';
import { ChatPanel } from '@/components/chat/ChatPanel';
import { ParagraphContent } from '@/components/paragraph/ParagraphContent';
import { ViewToggle, ViewMode } from '@/components/layout/ViewToggle';
import {
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  Loader2,
  AlertCircle,
  Sparkles,
} from 'lucide-react';

// Learning flow phases — state machine for paragraph completion
type LearningFlowPhase =
  | 'reading'
  | 'questions'
  | 'assessment'
  | 'chat'
  | 'reassessment'
  | 'completed';

type ContentTab = 'text' | 'audio' | 'cards' | 'practice' | 'exercises';

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

  // View mode: split, reading, chat (desktop only)
  const [viewMode, setViewMode] = useState<ViewMode>('split');
  const [activeTab, setActiveTab] = useState<ContentTab>('text');
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [showCompletion, setShowCompletion] = useState(false);
  const [showMobileSidebar, setShowMobileSidebar] = useState(false);
  const [showMobileChat, setShowMobileChat] = useState(false);
  const [pendingPrompt, setPendingPrompt] = useState<string | null>(null);

  // Learning flow state machine
  const [flowPhase, setFlowPhase] = useState<LearningFlowPhase>('reading');
  const [assessmentRound, setAssessmentRound] = useState(0);
  const [prerequisiteDismissed, setPrerequisiteDismissed] = useState(false);

  // Fetch paragraph data
  const { data: paragraph, isLoading, error } = useParagraphDetail(paragraphId);
  const { data: richContent } = useParagraphRichContent(paragraphId, locale as 'ru' | 'kz');
  const { data: navigation } = useParagraphNavigation(paragraphId);
  const { data: progress, refetch: refetchProgress } = useParagraphProgress(paragraphId);
  const { data: embeddedQuestions } = useEmbeddedQuestions(paragraphId);
  const { data: exercisesData } = useExercises(paragraphId);
  const { data: paragraphTest } = useParagraphTest(paragraph?.id);
  const { data: chapterParagraphs } = useChapterParagraphs(navigation?.chapter_id);
  const { data: prerequisiteCheck } = usePrerequisiteCheck(paragraphId);

  // Mutations
  const updateStepMutation = useUpdateParagraphStep(paragraphId);
  const submitAssessmentMutation = useSubmitSelfAssessment(paragraphId);
  const answerQuestionMutation = useAnswerEmbeddedQuestion(paragraphId);

  // Time tracking
  const lastSentRef = useRef<number>(Date.now());
  useEffect(() => { lastSentRef.current = Date.now(); }, [paragraphId]);

  const getAndResetElapsed = useCallback(() => {
    const now = Date.now();
    const elapsed = Math.min(Math.round((now - lastSentRef.current) / 1000), 3600);
    lastSentRef.current = now;
    return elapsed;
  }, []);

  // When flowPhase goes to 'chat', auto-switch to split mode
  useEffect(() => {
    if (flowPhase === 'chat') setViewMode('split');
  }, [flowPhase]);

  // Handle text selection → explain in chat
  const handleExplainSelection = useCallback((selectedText: string) => {
    const prompt = `Я выделил(а) этот фрагмент из параграфа:\n\n«${selectedText}»\n\nОбъясни мне это простыми словами.`;
    setPendingPrompt(prompt);
    setViewMode('split');
    setShowMobileChat(true);
  }, []);

  // Handle step change
  const handleStepChange = useCallback(async (step: ParagraphStep) => {
    try {
      await updateStepMutation.mutateAsync({ step, timeSpent: getAndResetElapsed() });
      if (step === 'content') setActiveTab('text');
      if (step === 'practice') setActiveTab('practice');
    } catch (error) {
      console.error('Failed to update step:', error);
    }
  }, [updateStepMutation, getAndResetElapsed]);

  // Handle "Завершить изучение" button click
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

  // Handle self-assessment
  const handleSelfAssessment = useCallback(async (rating: SelfAssessmentRating) => {
    const practiceScore =
      progress && progress.embedded_questions_total > 0
        ? (progress.embedded_questions_correct / progress.embedded_questions_total) * 100
        : null;
    const timeSpent = progress?.time_spent ?? null;

    await submitAssessmentMutation.mutateAsync({ rating, practice_score: practiceScore, time_spent: timeSpent });

    if (rating === 'understood') {
      await updateStepMutation.mutateAsync({ step: 'completed', timeSpent: getAndResetElapsed() });
      await refetchProgress();
      setFlowPhase('completed');
      setShowCompletion(true);
    } else {
      setFlowPhase('chat');
      // On mobile, open modal; on desktop, split view handles it
      setShowMobileChat(true);
    }
  }, [submitAssessmentMutation, updateStepMutation, refetchProgress, progress, getAndResetElapsed]);

  // Handle embedded question answer
  const handleAnswerQuestion = useCallback(async (questionId: number, answer: string | string[]): Promise<AnswerResult> => {
    return await answerQuestionMutation.mutateAsync({ questionId, answer });
  }, [answerQuestionMutation]);

  // Handle chat close — transition to reassessment
  const handleChatClose = useCallback(() => {
    setShowMobileChat(false);
    if (flowPhase === 'chat') {
      setAssessmentRound(prev => prev + 1);
      setFlowPhase('reassessment');
      setViewMode('reading');
    }
  }, [flowPhase]);

  // Handle next question
  const handleNextQuestion = useCallback(async () => {
    if (embeddedQuestions && currentQuestionIndex < embeddedQuestions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    } else if (flowPhase === 'questions') {
      await updateStepMutation.mutateAsync({ step: 'summary', timeSpent: getAndResetElapsed() });
      await refetchProgress();
      setFlowPhase('assessment');
    } else {
      handleStepChange('summary');
    }
  }, [embeddedQuestions, currentQuestionIndex, flowPhase, updateStepMutation, refetchProgress, handleStepChange, getAndResetElapsed]);

  // Completed count for mobile trigger
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

  // Embedded questions UI (shared between reading tab practice and flow questions phase)
  const questionsUI = embeddedQuestions && embeddedQuestions.length > 0 ? (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <h2 className="text-xl font-bold text-foreground mb-2">{t('practice.title')}</h2>
        <p className="text-muted-foreground">{t('practice.subtitle')}</p>
        {progress && progress.embedded_questions_answered === progress.embedded_questions_total && progress.embedded_questions_total > 0 && (
          <div className="mt-4 inline-flex items-center gap-2 bg-success/10 text-success px-4 py-2 rounded-full">
            <span className="font-medium">{t('practice.completed')}</span>
            <span className="text-sm">{t('practice.score', { correct: progress.embedded_questions_correct, total: progress.embedded_questions_total })}</span>
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
                index === currentQuestionIndex ? 'bg-primary scale-125' : 'bg-muted hover:bg-muted/80'
              }`}
            />
          ))}
        </div>
      )}
    </div>
  ) : null;

  // Should we show the content pane?
  const showContent = viewMode !== 'chat';
  // Should we show the chat pane? (desktop only)
  const showChatPanel = viewMode !== 'reading';

  return (
    <div className="flex flex-col h-full">
      {/* TopBar breadcrumbs + ViewToggle — rendered via portal-like pattern */}
      {/* We pass ViewToggle as a floating element since TopBar is in layout */}
      <div className="hidden md:flex items-center gap-4 px-6 py-2 bg-[#FFF8F2] border-b border-[#EDE8E3] flex-shrink-0">
        {/* Breadcrumbs */}
        <div className="flex items-center gap-1.5 text-[13px] font-semibold text-[#A09080] flex-1 min-w-0">
          {navigation && (
            <>
              <Link href={`/subjects/${navigation.textbook_id}`} className="hover:text-primary truncate max-w-[200px]">
                {navigation.textbook_title}
              </Link>
              <ChevronRight className="h-3 w-3 flex-shrink-0" />
              <Link href={`/chapters/${navigation.chapter_id}`} className="hover:text-primary">
                {t('chapterShort', { number: navigation.chapter_number })}
              </Link>
              <ChevronRight className="h-3 w-3 flex-shrink-0" />
              <span className="text-foreground">§{navigation.current_paragraph_number}</span>
            </>
          )}
        </div>

        <ViewToggle mode={viewMode} onChange={setViewMode} />
      </div>

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

      {/* Main split area */}
      <div className="flex flex-1 min-h-0 overflow-hidden h-full">
        {/* Left pane: Content */}
        {showContent && (
          <div className="flex-1 overflow-y-auto">
            <div className="mx-auto max-w-4xl px-4 py-6 pb-24 md:pb-8">
              {/* Mobile header */}
              <header className="mb-6 md:hidden">
                <div className="mb-4 flex items-center justify-between">
                  <Link
                    href={navigation ? `/chapters/${navigation.chapter_id}` : '/subjects'}
                    className="flex items-center gap-1 text-sm font-medium text-muted-foreground hover:text-foreground"
                  >
                    <ArrowLeft className="h-4 w-4" />
                    {tCommon('back')}
                  </Link>
                  {chapterParagraphs && (
                    <MobileSidebarTrigger
                      onClick={() => setShowMobileSidebar(true)}
                      paragraphsCount={chapterParagraphs.length}
                      completedCount={completedCount}
                    />
                  )}
                </div>
                {navigation && (
                  <nav className="mb-2 flex items-center gap-2 text-sm text-muted-foreground">
                    <Link href={`/subjects/${navigation.textbook_id}`} className="hover:text-primary truncate max-w-[120px]">
                      {navigation.textbook_title}
                    </Link>
                    <ChevronRight className="h-3 w-3 flex-shrink-0" />
                    <Link href={`/chapters/${navigation.chapter_id}`} className="hover:text-primary truncate max-w-[100px]">
                      {t('chapterShort', { number: navigation.chapter_number })}
                    </Link>
                    <ChevronRight className="h-3 w-3 flex-shrink-0" />
                    <span className="text-foreground font-medium">§{navigation.current_paragraph_number}</span>
                  </nav>
                )}
              </header>

              {/* Prerequisite Warning */}
              {prerequisiteCheck?.has_warnings && !prerequisiteDismissed && (
                <PrerequisiteWarning
                  warnings={prerequisiteCheck.warnings}
                  canProceed={prerequisiteCheck.can_proceed}
                  onProceedAnyway={() => setPrerequisiteDismissed(true)}
                />
              )}

              {/* Title */}
              <h1 className="text-2xl font-bold text-foreground md:text-3xl mb-6">
                §{paragraph.number}. {paragraph.title || t('untitled')}
              </h1>

              {/* Mobile progress indicator */}
              {navigation && (
                <div className="mb-6 card-flat p-3 md:hidden">
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span className="text-muted-foreground">{t('progressInChapter')}</span>
                    <span className="font-medium">{navigation.current_position_in_chapter} {t('of')} {navigation.total_paragraphs_in_chapter}</span>
                  </div>
                  <div className="flex gap-1">
                    {Array.from({ length: navigation.total_paragraphs_in_chapter }).map((_, i) => (
                      <div
                        key={i}
                        className={`h-2 flex-1 rounded-full transition-all ${
                          i + 1 < navigation.current_position_in_chapter ? 'bg-success'
                            : i + 1 === navigation.current_position_in_chapter ? 'bg-primary' : 'bg-muted'
                        }`}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* === PHASE: READING === */}
              {flowPhase === 'reading' && (
                <ParagraphContent
                  paragraph={paragraph}
                  richContent={richContent}
                  progress={progress}
                  embeddedQuestions={embeddedQuestions}
                  exercisesData={exercisesData}
                  paragraphId={paragraphId}
                  getMediaUrl={getMediaUrl}
                  activeTab={activeTab}
                  onTabChange={setActiveTab}
                  onExplainSelection={handleExplainSelection}
                  practiceContent={questionsUI}
                  quizContent={
                    paragraphTest && paragraph ? (
                      <section className="mb-8">
                        <ParagraphQuiz
                          test={paragraphTest}
                          paragraphId={paragraph.id}
                          onComplete={() => { refetchProgress(); }}
                        />
                      </section>
                    ) : undefined
                  }
                />
              )}

              {/* === PHASE: QUESTIONS === */}
              {flowPhase === 'questions' && questionsUI && (
                <section className="mb-8">{questionsUI}</section>
              )}

              {/* === PHASE: ASSESSMENT / REASSESSMENT === */}
              {(flowPhase === 'assessment' || flowPhase === 'reassessment') && (
                <section className="mb-8">
                  <SelfAssessment key={`assessment-${assessmentRound}`} onSubmit={handleSelfAssessment} />
                </section>
              )}

              {/* === PHASE: COMPLETED === */}
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
                  onGoToNext={() => { if (navigation.next_paragraph_id) router.push(`/paragraphs/${navigation.next_paragraph_id}`); }}
                  onGoToChapter={() => { router.push(`/chapters/${navigation.chapter_id}`); }}
                />
              )}

              {/* === NAVIGATION BAR === */}
              {!showCompletion && flowPhase !== 'questions' && flowPhase !== 'assessment' && flowPhase !== 'reassessment' && (
                <nav className="fixed bottom-0 left-0 right-0 bg-background/95 backdrop-blur border-t p-4 md:static md:border-0 md:bg-transparent md:p-0">
                  <div className="mx-auto max-w-4xl flex items-center justify-between gap-4">
                    {navigation?.previous_paragraph_id ? (
                      <Link
                        href={`/paragraphs/${navigation.previous_paragraph_id}`}
                        className="flex items-center gap-2 rounded-full bg-muted px-4 py-2 text-sm font-medium text-muted-foreground hover:bg-muted/80 hover:text-foreground transition-all"
                      >
                        <ChevronLeft className="h-4 w-4" />
                        <span className="hidden sm:inline">{t('previous')}</span>
                      </Link>
                    ) : <div />}

                    {navigation && (
                      <Link href={`/chapters/${navigation.chapter_id}`} className="text-sm text-muted-foreground hover:text-primary">
                        {t('backToChapter')}
                      </Link>
                    )}

                    {progress?.is_completed ? (
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
        )}

        {/* Right pane: Chat (desktop inline panel) */}
        {showChatPanel && (
          <div
            className={`hidden md:flex flex-col border-l border-[#EDE8E3] flex-shrink-0 transition-all ${
              viewMode === 'chat' ? 'w-full' : 'w-[360px]'
            }`}
          >
            <ChatPanel
              sessionType={flowPhase === 'chat' ? 'post_paragraph' : 'reading_help'}
              paragraphId={paragraphId}
              chapterId={navigation?.chapter_id}
              paragraphTitle={paragraph.title}
              paragraphNumber={paragraph.number}
              language={locale}
              onFlowClose={handleChatClose}
              initialPrompt={pendingPrompt}
              onInitialPromptSent={() => setPendingPrompt(null)}
            />
          </div>
        )}
      </div>

      {/* Mobile: Floating AI Chat Button */}
      {flowPhase !== 'chat' && !showCompletion && (
        <button
          onClick={() => setShowMobileChat(true)}
          className="fixed bottom-20 right-4 md:hidden z-40 flex items-center gap-2 px-4 py-3 bg-success text-white rounded-full shadow-lg hover:bg-success/90 hover:shadow-xl transition-all"
        >
          <Sparkles className="w-5 h-5" />
          <span className="font-medium">{tChat('floatingButton')}</span>
        </button>
      )}

      {/* Mobile: AI Chat Modal */}
      <div className="md:hidden">
        <ChatModal
          isOpen={showMobileChat}
          onClose={flowPhase === 'chat' ? handleChatClose : () => setShowMobileChat(false)}
          sessionType={flowPhase === 'chat' ? 'post_paragraph' : 'reading_help'}
          paragraphId={paragraphId}
          chapterId={navigation?.chapter_id}
        />
      </div>
    </div>
  );
}
