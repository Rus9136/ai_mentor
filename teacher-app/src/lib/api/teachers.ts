import { apiClient } from './client';

// ============================================================================
// Types
// ============================================================================

export interface MasteryDistribution {
  level_a: number;
  level_b: number;
  level_c: number;
  not_started: number;
}

export interface TeacherDashboardResponse {
  classes_count: number;
  total_students: number;
  students_by_level: MasteryDistribution;
  average_class_score: number;
  students_needing_help: number;
  recent_activity: RecentActivityItem[];
}

export interface RecentActivityItem {
  activity_type: string;
  student_name: string;
  description: string;
  timestamp: string;
}

export interface TeacherClassResponse {
  id: number;
  name: string;
  code: string;
  grade_level: number;
  academic_year: string;
  students_count: number;
  mastery_distribution: MasteryDistribution;
  average_score: number;
  progress_percentage: number;
}

export interface StudentWithMastery {
  id: number;
  student_code: string;
  first_name: string;
  last_name: string;
  middle_name: string | null;
  mastery_level: string | null;
  mastery_score: number | null;
  completed_paragraphs: number;
  total_paragraphs: number;
  progress_percentage: number;
  last_activity: string | null;
}

export interface TeacherClassDetailResponse {
  id: number;
  name: string;
  code: string;
  grade_level: number;
  academic_year: string;
  description: string | null;
  students_count: number;
  mastery_distribution: MasteryDistribution;
  average_score: number;
  progress_percentage: number;
  students: StudentWithMastery[];
}

export interface ChapterProgressBrief {
  chapter_id: number;
  chapter_title: string;
  chapter_number: number;
  mastery_level: string | null;
  mastery_score: number | null;
  completed_paragraphs: number;
  total_paragraphs: number;
  progress_percentage: number;
}

export interface ClassOverviewResponse {
  class_info: TeacherClassResponse;
  chapters_progress: ChapterProgressBrief[];
  trend: string;
  trend_percentage: number;
}

export interface StudentBriefResponse {
  id: number;
  student_code: string;
  grade_level: number;
  first_name: string;
  last_name: string;
  middle_name: string | null;
}

export interface TestAttemptBrief {
  id: number;
  test_id: number;
  test_title: string;
  score: number;
  max_score: number;
  percentage: number;
  completed_at: string;
}

export interface StudentProgressDetailResponse {
  student: StudentBriefResponse;
  class_name: string;
  overall_mastery_level: string | null;
  overall_mastery_score: number;
  total_time_spent: number;
  chapters_progress: ChapterProgressBrief[];
  recent_tests: TestAttemptBrief[];
  last_activity: string | null;
  days_since_last_activity: number;
}

export interface MasteryHistoryItem {
  id: number;
  recorded_at: string;
  previous_level: string | null;
  new_level: string | null;
  previous_score: number | null;
  new_score: number | null;
  chapter_id: number | null;
  paragraph_id: number | null;
  test_attempt_id: number | null;
}

export interface MasteryHistoryResponse {
  student_id: number;
  student_name: string;
  history: MasteryHistoryItem[];
}

export interface StrugglingTopicResponse {
  paragraph_id: number;
  paragraph_title: string;
  chapter_id: number;
  chapter_title: string;
  struggling_count: number;
  total_students: number;
  struggling_percentage: number;
  average_score: number;
}

export interface ClassTrend {
  class_id: number;
  class_name: string;
  previous_average: number;
  current_average: number;
  change_percentage: number;
  trend: string;
  promoted_to_a: number;
  demoted_to_c: number;
}

export interface MasteryTrendsResponse {
  period: string;
  start_date: string;
  end_date: string;
  overall_trend: string;
  overall_change_percentage: number;
  class_trends: ClassTrend[];
}

// ============================================================================
// API Functions
// ============================================================================

// Dashboard
export async function getDashboard(): Promise<TeacherDashboardResponse> {
  const response = await apiClient.get<TeacherDashboardResponse>('/teachers/dashboard');
  return response.data;
}

// Classes
export async function getClasses(): Promise<TeacherClassResponse[]> {
  const response = await apiClient.get<TeacherClassResponse[]>('/teachers/classes');
  return response.data;
}

export async function getClassDetail(classId: number): Promise<TeacherClassDetailResponse> {
  const response = await apiClient.get<TeacherClassDetailResponse>(`/teachers/classes/${classId}`);
  return response.data;
}

export async function getClassOverview(classId: number): Promise<ClassOverviewResponse> {
  const response = await apiClient.get<ClassOverviewResponse>(`/teachers/classes/${classId}/overview`);
  return response.data;
}

// Student Progress
export async function getStudentProgress(
  classId: number,
  studentId: number
): Promise<StudentProgressDetailResponse> {
  const response = await apiClient.get<StudentProgressDetailResponse>(
    `/teachers/classes/${classId}/students/${studentId}/progress`
  );
  return response.data;
}

export async function getMasteryHistory(studentId: number): Promise<MasteryHistoryResponse> {
  const response = await apiClient.get<MasteryHistoryResponse>(
    `/teachers/students/${studentId}/mastery-history`
  );
  return response.data;
}

// Analytics
export async function getStrugglingTopics(): Promise<StrugglingTopicResponse[]> {
  const response = await apiClient.get<StrugglingTopicResponse[]>(
    '/teachers/analytics/struggling-topics'
  );
  return response.data;
}

export async function getMasteryTrends(
  period: 'weekly' | 'monthly' = 'weekly'
): Promise<MasteryTrendsResponse> {
  const response = await apiClient.get<MasteryTrendsResponse>(
    `/teachers/analytics/mastery-trends?period=${period}`
  );
  return response.data;
}
