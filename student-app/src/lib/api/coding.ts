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
