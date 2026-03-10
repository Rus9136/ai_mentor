import { apiClient } from './client';

// =============================================================================
// Types - matching backend PrerequisiteCheckResponse
// =============================================================================

export interface PrerequisiteWarning {
  paragraph_id: number;
  paragraph_title: string | null;
  paragraph_number: number | null;
  chapter_title: string | null;
  textbook_title: string | null;
  grade_level: number | null;
  current_score: number;
  strength: 'required' | 'recommended';
  recommendation: 'review_first' | 'consider_review';
}

export interface PrerequisiteCheckResponse {
  paragraph_id: number;
  has_warnings: boolean;
  warnings: PrerequisiteWarning[];
  can_proceed: boolean;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Check if student meets prerequisites for a paragraph.
 */
export async function checkPrerequisites(paragraphId: number): Promise<PrerequisiteCheckResponse> {
  const response = await apiClient.get<PrerequisiteCheckResponse>(
    `/students/paragraphs/${paragraphId}/prerequisites`
  );
  return response.data;
}
