/**
 * Homework API functions for teacher-app.
 */
import { apiClient } from './client';
import type {
  HomeworkCreate,
  HomeworkUpdate,
  HomeworkResponse,
  HomeworkListResponse,
  HomeworkListParams,
  HomeworkTaskCreate,
  HomeworkTaskResponse,
  QuestionCreate,
  QuestionResponseWithAnswer,
  GenerationParams,
  AnswerForReview,
  ReviewQueueParams,
  TeacherReviewRequest,
  TeacherReviewResponse,
  Attachment,
} from '@/types/homework';

// =============================================================================
// Homework CRUD
// =============================================================================

export async function createHomework(data: HomeworkCreate): Promise<HomeworkResponse> {
  const response = await apiClient.post<HomeworkResponse>('/teachers/homework', data);
  return response.data;
}

export async function listHomework(params?: HomeworkListParams): Promise<HomeworkListResponse[]> {
  const response = await apiClient.get<HomeworkListResponse[]>('/teachers/homework', { params });
  return response.data;
}

export async function getHomework(homeworkId: number): Promise<HomeworkResponse> {
  const response = await apiClient.get<HomeworkResponse>(`/teachers/homework/${homeworkId}`);
  return response.data;
}

export async function updateHomework(
  homeworkId: number,
  data: HomeworkUpdate
): Promise<HomeworkResponse> {
  const response = await apiClient.put<HomeworkResponse>(`/teachers/homework/${homeworkId}`, data);
  return response.data;
}

export async function deleteHomework(homeworkId: number): Promise<void> {
  await apiClient.delete(`/teachers/homework/${homeworkId}`);
}

// =============================================================================
// Homework Status Actions
// =============================================================================

export async function publishHomework(
  homeworkId: number,
  studentIds?: number[]
): Promise<HomeworkResponse> {
  const response = await apiClient.post<HomeworkResponse>(
    `/teachers/homework/${homeworkId}/publish`,
    studentIds ? { student_ids: studentIds } : undefined
  );
  return response.data;
}

export async function closeHomework(homeworkId: number): Promise<HomeworkResponse> {
  const response = await apiClient.post<HomeworkResponse>(
    `/teachers/homework/${homeworkId}/close`
  );
  return response.data;
}

// =============================================================================
// Tasks
// =============================================================================

export async function addTask(
  homeworkId: number,
  data: HomeworkTaskCreate
): Promise<HomeworkTaskResponse> {
  const response = await apiClient.post<HomeworkTaskResponse>(
    `/teachers/homework/${homeworkId}/tasks`,
    data
  );
  return response.data;
}

export async function deleteTask(taskId: number): Promise<void> {
  await apiClient.delete(`/teachers/homework/tasks/${taskId}`);
}

// =============================================================================
// Questions
// =============================================================================

export async function addQuestion(
  taskId: number,
  data: QuestionCreate
): Promise<QuestionResponseWithAnswer> {
  const response = await apiClient.post<QuestionResponseWithAnswer>(
    `/teachers/homework/tasks/${taskId}/questions`,
    data
  );
  return response.data;
}

export async function generateQuestions(
  taskId: number,
  params?: GenerationParams,
  regenerate: boolean = false
): Promise<QuestionResponseWithAnswer[]> {
  // Backend expects:
  // - params (GenerationParams) as request body
  // - regenerate as query parameter
  const response = await apiClient.post<QuestionResponseWithAnswer[]>(
    `/teachers/homework/tasks/${taskId}/generate-questions`,
    params || undefined,
    { params: { regenerate } }
  );
  return response.data;
}

// =============================================================================
// Teacher Review
// =============================================================================

export async function getReviewQueue(params?: ReviewQueueParams): Promise<AnswerForReview[]> {
  const response = await apiClient.get<AnswerForReview[]>('/teachers/homework/review-queue', {
    params,
  });
  return response.data;
}

export async function reviewAnswer(
  answerId: number,
  data: TeacherReviewRequest
): Promise<TeacherReviewResponse> {
  const response = await apiClient.post<TeacherReviewResponse>(
    `/teachers/homework/answers/${answerId}/review`,
    data
  );
  return response.data;
}

// =============================================================================
// File Upload
// =============================================================================

export async function uploadHomeworkFile(file: File): Promise<Attachment> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<Attachment>('/teachers/homework/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
}

// =============================================================================
// Content (for ContentSelector)
// =============================================================================

export interface TextbookBrief {
  id: number;
  title: string;
  subject: string;
  grade_level: number;
}

export interface ChapterBrief {
  id: number;
  number: number;
  title: string;
}

export interface ParagraphBrief {
  id: number;
  number: number;
  title: string;
}

// Pagination response type
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export async function getTextbooks(): Promise<TextbookBrief[]> {
  const response = await apiClient.get<PaginatedResponse<TextbookBrief>>('/teachers/textbooks');
  return response.data.items;
}

export async function getChapters(textbookId: number): Promise<ChapterBrief[]> {
  const response = await apiClient.get<PaginatedResponse<ChapterBrief>>(`/teachers/textbooks/${textbookId}/chapters`);
  return response.data.items;
}

export async function getParagraphs(chapterId: number): Promise<ParagraphBrief[]> {
  const response = await apiClient.get<PaginatedResponse<ParagraphBrief>>(`/teachers/chapters/${chapterId}/paragraphs`);
  return response.data.items;
}
