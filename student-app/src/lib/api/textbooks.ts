import { apiClient } from './client';

// =============================================================================
// Types - matching backend schemas
// =============================================================================

/**
 * Brief subject info for embedding in responses.
 * Matches backend SubjectBrief schema.
 */
export interface SubjectBrief {
  id: number;
  code: string;
  name_ru: string;
  name_kz: string;
}

export interface TextbookProgress {
  chapters_total: number;
  chapters_completed: number;
  paragraphs_total: number;
  paragraphs_completed: number;
  percentage: number;
}

export interface StudentTextbook {
  id: number;
  title: string;
  subject_id: number | null;  // Normalized subject ID (FK)
  subject: string;            // Subject name (backward compatibility)
  subject_rel: SubjectBrief | null;  // Full subject details
  grade_level: number;
  description: string | null;
  is_global: boolean;
  progress: TextbookProgress;
  mastery_level: 'A' | 'B' | 'C' | null;
  last_activity: string | null;
  author: string | null;
  chapters_count: number;
}

export interface ChapterProgress {
  paragraphs_total: number;
  paragraphs_completed: number;
  percentage: number;
}

export interface StudentChapter {
  id: number;
  textbook_id: number;
  title: string;
  number: number;
  order: number;
  description: string | null;
  learning_objective: string | null;
  status: 'completed' | 'in_progress' | 'not_started' | 'locked';
  progress: ChapterProgress;
  mastery_level: 'A' | 'B' | 'C' | null;
  mastery_score: number | null;
  has_summative_test: boolean;
  summative_passed: boolean | null;
}

export interface StudentParagraph {
  id: number;
  chapter_id: number;
  title: string | null;
  number: number;
  order: number;
  summary: string | null;
  status: 'completed' | 'in_progress' | 'not_started';
  estimated_time: number;
  has_practice: boolean;
  practice_score: number | null;
  learning_objective: string | null;
  key_terms: string[] | null;
}

export interface ParagraphDetail {
  id: number;
  chapter_id: number;
  title: string | null;
  number: number;
  order: number;
  content: string;
  summary: string | null;
  learning_objective: string | null;
  lesson_objective: string | null;
  key_terms: string[] | null;
  questions: Record<string, unknown>[] | null;
  status: string;
  current_step: string | null;
  has_audio: boolean;
  has_video: boolean;
  has_slides: boolean;
  has_cards: boolean;
  chapter_title: string | null;
  textbook_title: string | null;
}

export interface FlashCard {
  id: string;
  type: string;
  front: string;
  back: string;
  order: number;
}

export interface ParagraphRichContent {
  paragraph_id: number;
  language: string;
  explain_text: string | null;
  audio_url: string | null;
  video_url: string | null;
  slides_url: string | null;
  cards: FlashCard[] | null;
  has_explain: boolean;
  has_audio: boolean;
  has_video: boolean;
  has_slides: boolean;
  has_cards: boolean;
}

export interface ParagraphNavigation {
  current_paragraph_id: number;
  current_paragraph_number: number;
  current_paragraph_title: string | null;
  chapter_id: number;
  chapter_title: string;
  chapter_number: number;
  textbook_id: number;
  textbook_title: string;
  previous_paragraph_id: number | null;
  next_paragraph_id: number | null;
  total_paragraphs_in_chapter: number;
  current_position_in_chapter: number;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Get all textbooks available to the student with progress.
 */
export async function getStudentTextbooks(): Promise<StudentTextbook[]> {
  const response = await apiClient.get<StudentTextbook[]>('/students/textbooks');
  return response.data;
}

/**
 * Get chapters for a textbook with student's progress.
 */
export async function getTextbookChapters(textbookId: number): Promise<StudentChapter[]> {
  const response = await apiClient.get<StudentChapter[]>(
    `/students/textbooks/${textbookId}/chapters`
  );
  return response.data;
}

/**
 * Get paragraphs for a chapter with student's progress.
 */
export async function getChapterParagraphs(chapterId: number): Promise<StudentParagraph[]> {
  const response = await apiClient.get<StudentParagraph[]>(
    `/students/chapters/${chapterId}/paragraphs`
  );
  return response.data;
}

/**
 * Get full paragraph detail for learning.
 */
export async function getParagraphDetail(paragraphId: number): Promise<ParagraphDetail> {
  const response = await apiClient.get<ParagraphDetail>(
    `/students/paragraphs/${paragraphId}`
  );
  return response.data;
}

// Маппинг URL локали на API параметр
// URL использует 'kz', но API принимает 'kk'
const urlLocaleToApiLocale = (locale: string): string => (locale === 'kz' ? 'kk' : locale);

/**
 * Get rich content for a paragraph (audio, video, slides, cards).
 */
export async function getParagraphRichContent(
  paragraphId: number,
  language: 'ru' | 'kz' = 'ru'
): Promise<ParagraphRichContent> {
  const response = await apiClient.get<ParagraphRichContent>(
    `/students/paragraphs/${paragraphId}/content`,
    { params: { language: urlLocaleToApiLocale(language) } }
  );
  return response.data;
}

/**
 * Get navigation context for paragraph learning view.
 */
export async function getParagraphNavigation(paragraphId: number): Promise<ParagraphNavigation> {
  const response = await apiClient.get<ParagraphNavigation>(
    `/students/paragraphs/${paragraphId}/navigation`
  );
  return response.data;
}

// =============================================================================
// Progress & Step Tracking Types
// =============================================================================

export type ParagraphStep = 'intro' | 'content' | 'practice' | 'summary' | 'completed';
export type SelfAssessmentRating = 'understood' | 'questions' | 'difficult';

export interface ParagraphProgress {
  paragraph_id: number;
  is_completed: boolean;
  current_step: ParagraphStep;
  time_spent: number;
  last_accessed_at: string | null;
  completed_at: string | null;
  self_assessment: SelfAssessmentRating | null;
  self_assessment_at: string | null;
  available_steps: ParagraphStep[];
  embedded_questions_total: number;
  embedded_questions_answered: number;
  embedded_questions_correct: number;
}

export interface StepProgressResponse {
  paragraph_id: number;
  current_step: ParagraphStep;
  is_completed: boolean;
  time_spent: number;
  available_steps: ParagraphStep[];
  self_assessment: SelfAssessmentRating | null;
}

export interface SelfAssessmentResponse {
  paragraph_id: number;
  rating: SelfAssessmentRating;
  recorded_at: string;
  message: string;
}

// =============================================================================
// Embedded Questions Types
// =============================================================================

export interface EmbeddedQuestionOption {
  id: string;
  text: string;
}

export interface EmbeddedQuestion {
  id: number;
  paragraph_id: number;
  question_text: string;
  question_type: 'single_choice' | 'multiple_choice' | 'true_false';
  options: EmbeddedQuestionOption[] | null;
  hint: string | null;
  sort_order: number;
}

export interface AnswerResult {
  is_correct: boolean;
  correct_answer: string | string[] | null;
  explanation: string | null;
  attempts_count: number;
}

// =============================================================================
// Progress & Embedded Questions API Functions
// =============================================================================

/**
 * Get student's progress for a paragraph including step tracking.
 */
export async function getParagraphProgress(paragraphId: number): Promise<ParagraphProgress> {
  const response = await apiClient.get<ParagraphProgress>(
    `/students/paragraphs/${paragraphId}/progress`
  );
  return response.data;
}

/**
 * Update student's current step in a paragraph.
 */
export async function updateParagraphStep(
  paragraphId: number,
  step: ParagraphStep,
  timeSpent?: number
): Promise<StepProgressResponse> {
  const response = await apiClient.post<StepProgressResponse>(
    `/students/paragraphs/${paragraphId}/progress`,
    { step, time_spent: timeSpent }
  );
  return response.data;
}

/**
 * Submit self-assessment for a paragraph.
 */
export async function submitSelfAssessment(
  paragraphId: number,
  rating: SelfAssessmentRating
): Promise<SelfAssessmentResponse> {
  const response = await apiClient.post<SelfAssessmentResponse>(
    `/students/paragraphs/${paragraphId}/self-assessment`,
    { rating }
  );
  return response.data;
}

/**
 * Get embedded questions for a paragraph (without correct answers).
 */
export async function getEmbeddedQuestions(paragraphId: number): Promise<EmbeddedQuestion[]> {
  const response = await apiClient.get<EmbeddedQuestion[]>(
    `/students/paragraphs/${paragraphId}/embedded-questions`
  );
  return response.data;
}

/**
 * Submit answer to an embedded question.
 */
export async function answerEmbeddedQuestion(
  questionId: number,
  answer: string | string[]
): Promise<AnswerResult> {
  const response = await apiClient.post<AnswerResult>(
    `/students/embedded-questions/${questionId}/answer`,
    { answer }
  );
  return response.data;
}
