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
  textbook_title?: string;
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

// Analytics Summary
export interface AnalyticsSummaryResponse {
  total_students: number;
  average_mastery: number;
  struggling_topics_count: number;
  metacognitive_alerts_count: number;
  active_students_count: number;
}

// Paragraph Assessment Detail
export interface ParagraphAssessmentStudent {
  student_id: number;
  first_name: string;
  last_name: string;
  rating: string;
  practice_score: number | null;
  mastery_impact: number;
  created_at: string;
}

export interface ParagraphAssessmentDetailResponse {
  paragraph_id: number;
  paragraph_title: string;
  students: ParagraphAssessmentStudent[];
}

// Self-Assessment Analytics
export interface SelfAssessmentParagraphSummary {
  paragraph_id: number;
  paragraph_title: string;
  chapter_id: number;
  chapter_title: string;
  total_assessments: number;
  understood_count: number;
  questions_count: number;
  difficult_count: number;
  understood_pct: number;
  questions_pct: number;
  difficult_pct: number;
}

export interface SelfAssessmentSummaryResponse {
  total_assessments: number;
  total_students: number;
  paragraphs: SelfAssessmentParagraphSummary[];
}

export interface MetacognitiveAlertStudent {
  student_id: number;
  student_code: string;
  first_name: string;
  last_name: string;
  paragraph_id: number;
  paragraph_title: string;
  rating: string;
  practice_score: number;
  mastery_impact: number;
  created_at: string;
}

export interface MetacognitiveAlertsResponse {
  overconfident: MetacognitiveAlertStudent[];
  underconfident: MetacognitiveAlertStudent[];
}

export interface StudentSelfAssessmentItem {
  id: number;
  paragraph_id: number;
  paragraph_title: string;
  chapter_title: string;
  rating: string;
  practice_score: number | null;
  mastery_impact: number;
  mismatch_type: string | null;
  created_at: string;
}

export interface StudentSelfAssessmentHistory {
  student_id: number;
  student_name: string;
  total_assessments: number;
  adequate_count: number;
  overconfident_count: number;
  underconfident_count: number;
  assessments: StudentSelfAssessmentItem[];
}

// Diagnostic Results
export interface DiagnosticStudentResult {
  student_id: number;
  student_code: string;
  first_name: string;
  last_name: string;
  attempt_id: number;
  test_id: number;
  test_title: string;
  textbook_title: string | null;
  subject_name: string | null;
  score: number | null;
  score_percent: number | null;
  passed: boolean | null;
  completed_at: string | null;
  time_spent: number | null;
  questions_total: number;
  questions_correct: number;
}

export interface DiagnosticScoreDistribution {
  range_0_40: number;
  range_40_60: number;
  range_60_85: number;
  range_85_100: number;
}

export interface DiagnosticResultsResponse {
  total_students: number;
  students_tested: number;
  average_score: number | null;
  distribution: DiagnosticScoreDistribution;
  results: DiagnosticStudentResult[];
}

export interface DiagnosticAnswerDetail {
  question_id: number;
  question_text: string;
  question_type: string;
  options: { id: number; text: string; is_correct: boolean }[];
  selected_option_ids: number[] | null;
  answer_text: string | null;
  is_correct: boolean | null;
  points_earned: number | null;
  points_possible: number;
  explanation: string | null;
}

export interface DiagnosticAttemptAnswersResponse {
  attempt_id: number;
  test_id: number;
  test_title: string;
  student_id: number;
  student_name: string;
  score: number | null;
  passed: boolean | null;
  completed_at: string | null;
  time_spent: number | null;
  answers: DiagnosticAnswerDetail[];
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
  const response = await apiClient.get<{ items: TeacherClassResponse[]; total: number }>('/teachers/classes');
  return response.data.items;
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
export async function getAnalyticsSummary(classId?: number): Promise<AnalyticsSummaryResponse> {
  const params = classId ? `?class_id=${classId}` : '';
  const response = await apiClient.get<AnalyticsSummaryResponse>(
    `/teachers/analytics/summary${params}`
  );
  return response.data;
}

export async function getStrugglingTopics(classId?: number): Promise<StrugglingTopicResponse[]> {
  const params = classId ? `?class_id=${classId}` : '';
  const response = await apiClient.get<{ items: StrugglingTopicResponse[]; total: number }>(
    `/teachers/analytics/struggling-topics${params}`
  );
  return response.data.items;
}

export async function getMasteryTrends(
  period: 'weekly' | 'monthly' = 'weekly',
  classId?: number
): Promise<MasteryTrendsResponse> {
  const params = new URLSearchParams({ period });
  if (classId) params.set('class_id', String(classId));
  const response = await apiClient.get<MasteryTrendsResponse>(
    `/teachers/analytics/mastery-trends?${params}`
  );
  return response.data;
}

// Self-Assessment Analytics
export async function getSelfAssessmentSummary(classId?: number): Promise<SelfAssessmentSummaryResponse> {
  const params = classId ? `?class_id=${classId}` : '';
  const response = await apiClient.get<SelfAssessmentSummaryResponse>(
    `/teachers/analytics/self-assessment-summary${params}`
  );
  return response.data;
}

export async function getParagraphAssessments(
  paragraphId: number,
  classId?: number
): Promise<ParagraphAssessmentDetailResponse> {
  const params = classId ? `?class_id=${classId}` : '';
  const response = await apiClient.get<ParagraphAssessmentDetailResponse>(
    `/teachers/analytics/paragraph/${paragraphId}/assessments${params}`
  );
  return response.data;
}

export async function getMetacognitiveAlerts(classId?: number): Promise<MetacognitiveAlertsResponse> {
  const params = classId ? `?class_id=${classId}` : '';
  const response = await apiClient.get<MetacognitiveAlertsResponse>(
    `/teachers/analytics/metacognitive-alerts${params}`
  );
  return response.data;
}

export async function getStudentSelfAssessments(
  studentId: number
): Promise<StudentSelfAssessmentHistory> {
  const response = await apiClient.get<StudentSelfAssessmentHistory>(
    `/teachers/students/${studentId}/self-assessments`
  );
  return response.data;
}

// Diagnostic Analytics
export async function getDiagnosticResults(classId?: number): Promise<DiagnosticResultsResponse> {
  const params = classId ? `?class_id=${classId}` : '';
  const response = await apiClient.get<DiagnosticResultsResponse>(
    `/teachers/analytics/diagnostic-results${params}`
  );
  return response.data;
}

export async function getDiagnosticAttemptAnswers(
  attemptId: number
): Promise<DiagnosticAttemptAnswersResponse> {
  const response = await apiClient.get<DiagnosticAttemptAnswersResponse>(
    `/teachers/analytics/diagnostic-results/${attemptId}/answers`
  );
  return response.data;
}
