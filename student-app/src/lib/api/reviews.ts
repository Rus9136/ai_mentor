import { apiClient } from './client';

// =============================================================================
// Types - matching backend review_schedule schemas
// =============================================================================

export interface ReviewItem {
  id: number;
  paragraph_id: number;
  paragraph_title: string | null;
  paragraph_number: string | null;
  chapter_title: string | null;
  textbook_title: string | null;
  streak: number;
  next_review_date: string;
  last_review_date: string | null;
  total_reviews: number;
  successful_reviews: number;
  best_score: number | null;
  effective_score: number | null;
}

export interface DueReviewsResponse {
  due_today: ReviewItem[];
  due_today_count: number;
  upcoming_week_count: number;
  total_active: number;
}

export interface ReviewResultResponse {
  paragraph_id: number;
  passed: boolean;
  score: number;
  new_streak: number;
  next_review_date: string;
  message: string;
}

export interface ReviewStats {
  total_active_reviews: number;
  due_today: number;
  due_this_week: number;
  total_completed_reviews: number;
  success_rate: number;
  average_streak: number;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Get reviews due for today.
 */
export async function getDueReviews(): Promise<DueReviewsResponse> {
  const response = await apiClient.get<DueReviewsResponse>('/students/reviews/due');
  return response.data;
}

/**
 * Submit review result for a paragraph.
 */
export async function completeReview(paragraphId: number, score: number): Promise<ReviewResultResponse> {
  const response = await apiClient.post<ReviewResultResponse>(
    `/students/reviews/${paragraphId}/complete`,
    { score }
  );
  return response.data;
}

/**
 * Get spaced repetition stats.
 */
export async function getReviewStats(): Promise<ReviewStats> {
  const response = await apiClient.get<ReviewStats>('/students/reviews/stats');
  return response.data;
}
