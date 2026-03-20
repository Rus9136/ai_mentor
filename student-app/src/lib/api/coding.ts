/**
 * Student Coding Challenges API
 */

import { apiClient } from './client';

// =============================================================================
// Types
// =============================================================================

export interface CodingTopic {
  id: number;
  title: string;
  title_kk: string | null;
  slug: string;
  description: string | null;
  description_kk: string | null;
  sort_order: number;
  icon: string | null;
  grade_level: number | null;
  is_active: boolean;
  total_challenges: number;
  solved_challenges: number;
}

export interface ChallengeListItem {
  id: number;
  title: string;
  title_kk: string | null;
  difficulty: 'easy' | 'medium' | 'hard';
  points: number;
  sort_order: number;
  status: 'not_started' | 'attempted' | 'solved';
}

export interface TestCase {
  input: string;
  expected_output: string;
  description: string | null;
  is_hidden: boolean;
}

export interface CodingSubmission {
  id: number;
  challenge_id: number;
  code: string;
  status: 'passed' | 'failed' | 'error' | 'timeout';
  tests_passed: number;
  tests_total: number;
  execution_time_ms: number | null;
  error_message: string | null;
  attempt_number: number;
  xp_earned: number;
  created_at: string;
}

export interface ChallengeDetail {
  id: number;
  topic_id: number;
  title: string;
  title_kk: string | null;
  description: string;
  description_kk: string | null;
  difficulty: 'easy' | 'medium' | 'hard';
  points: number;
  starter_code: string | null;
  hints: string[];
  hints_kk: string[];
  test_cases: TestCase[];
  time_limit_ms: number | null;
  status: 'not_started' | 'attempted' | 'solved';
  best_submission: CodingSubmission | null;
}

export interface SubmitSolutionRequest {
  code: string;
  tests_passed: number;
  tests_total: number;
  execution_time_ms?: number;
  error_message?: string;
}

export interface CodingStats {
  total_solved: number;
  total_attempts: number;
  total_xp: number;
  topics_progress: CodingTopic[];
}

// =============================================================================
// API Functions
// =============================================================================

const BASE = '/students/coding';

export async function listTopics(): Promise<CodingTopic[]> {
  const { data } = await apiClient.get(`${BASE}/topics`);
  return data;
}

export async function listChallenges(
  topicSlug: string
): Promise<ChallengeListItem[]> {
  const { data } = await apiClient.get(
    `${BASE}/topics/${topicSlug}/challenges`
  );
  return data;
}

export async function getChallengeDetail(
  challengeId: number
): Promise<ChallengeDetail> {
  const { data } = await apiClient.get(`${BASE}/challenges/${challengeId}`);
  return data;
}

export async function submitSolution(
  challengeId: number,
  body: SubmitSolutionRequest
): Promise<CodingSubmission> {
  const { data } = await apiClient.post(
    `${BASE}/challenges/${challengeId}/submit`,
    body
  );
  return data;
}

export async function listSubmissions(
  challengeId: number
): Promise<CodingSubmission[]> {
  const { data } = await apiClient.get(
    `${BASE}/challenges/${challengeId}/submissions`
  );
  return data;
}

export async function getCodingStats(): Promise<CodingStats> {
  const { data } = await apiClient.get(`${BASE}/stats`);
  return data;
}

// =============================================================================
// Course Types
// =============================================================================

export interface CodingCourse {
  id: number;
  title: string;
  title_kk: string | null;
  description: string | null;
  description_kk: string | null;
  slug: string;
  grade_level: number | null;
  total_lessons: number;
  estimated_hours: number | null;
  sort_order: number;
  icon: string | null;
  is_active: boolean;
  completed_lessons: number;
  last_lesson_id: number | null;
  started: boolean;
  completed: boolean;
}

export interface LessonListItem {
  id: number;
  title: string;
  title_kk: string | null;
  sort_order: number;
  has_challenge: boolean;
  challenge_id: number | null;
  is_completed: boolean;
}

export interface LessonDetail {
  id: number;
  course_id: number;
  title: string;
  title_kk: string | null;
  sort_order: number;
  theory_content: string;
  theory_content_kk: string | null;
  starter_code: string | null;
  challenge_id: number | null;
  challenge: ChallengeDetail | null;
  is_completed: boolean;
}

export interface LessonCompleteResponse {
  lesson_id: number;
  course_id: number;
  completed_lessons: number;
  total_lessons: number;
  course_completed: boolean;
}

// =============================================================================
// Course API Functions
// =============================================================================

export async function listCourses(): Promise<CodingCourse[]> {
  const { data } = await apiClient.get(`${BASE}/courses`);
  return data;
}

export async function listLessons(
  courseSlug: string
): Promise<LessonListItem[]> {
  const { data } = await apiClient.get(
    `${BASE}/courses/${courseSlug}/lessons`
  );
  return data;
}

export async function getLessonDetail(
  lessonId: number
): Promise<LessonDetail> {
  const { data } = await apiClient.get(`${BASE}/courses/lessons/${lessonId}`);
  return data;
}

export async function completeLesson(
  lessonId: number
): Promise<LessonCompleteResponse> {
  const { data } = await apiClient.post(
    `${BASE}/courses/lessons/${lessonId}/complete`
  );
  return data;
}
