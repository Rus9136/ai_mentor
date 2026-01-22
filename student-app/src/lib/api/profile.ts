import { apiClient } from './client';

// =============================================================================
// Types - matching backend schemas
// =============================================================================

export interface StudentStats {
  streak_days: number;
  total_paragraphs_completed: number;
  total_tasks_completed: number;
  total_time_spent_minutes: number;
}

export interface ClassInfo {
  id: number;
  name: string;
  grade_level: number;
}

export interface StudentProfile {
  id: number;
  student_code: string;
  grade_level: number;
  birth_date: string | null;
  school_name: string | null;
  classes: ClassInfo[];
}

export interface ChapterMasteryDetail {
  id: number;
  student_id: number;
  chapter_id: number;
  total_paragraphs: number;
  completed_paragraphs: number;
  mastered_paragraphs: number;
  struggling_paragraphs: number;
  average_score: number | null;
  weighted_score: number | null;
  summative_score: number | null;
  summative_passed: boolean | null;
  mastery_level: 'A' | 'B' | 'C';
  mastery_score: number;
  progress_percentage: number;
  estimated_completion_date: string | null;
  last_updated_at: string;
  chapter_title: string | null;
  chapter_order: number | null;
}

export interface MasteryOverview {
  student_id: number;
  chapters: ChapterMasteryDetail[];
  total_chapters: number;
  average_mastery_score: number;
  level_a_count: number;
  level_b_count: number;
  level_c_count: number;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Get student's overall stats (streak, paragraphs completed, tasks, time spent).
 */
export async function getStudentStats(): Promise<StudentStats> {
  const response = await apiClient.get<StudentStats>('/students/stats');
  return response.data;
}

/**
 * Get mastery overview across all chapters with A/B/C levels.
 */
export async function getMasteryOverview(): Promise<MasteryOverview> {
  const response = await apiClient.get<MasteryOverview>('/students/mastery/overview');
  return response.data;
}

/**
 * Get student's profile with class information.
 */
export async function getStudentProfile(): Promise<StudentProfile> {
  const response = await apiClient.get<StudentProfile>('/students/profile');
  return response.data;
}
