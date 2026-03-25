import { useQuery } from '@tanstack/react-query';
import {
  getDashboard,
  getClasses,
  getClassDetail,
  getClassOverview,
  getStudentProgress,
  getMasteryHistory,
  getAnalyticsSummary,
  getStrugglingTopics,
  getMasteryTrends,
  getSelfAssessmentSummary,
  getMetacognitiveAlerts,
  getStudentSelfAssessments,
  getDiagnosticResults,
  getDiagnosticAttemptAnswers,
} from '@/lib/api/teachers';

// Dashboard
export function useDashboard() {
  return useQuery({
    queryKey: ['teacher', 'dashboard'],
    queryFn: getDashboard,
  });
}

// Classes
export function useClasses() {
  return useQuery({
    queryKey: ['teacher', 'classes'],
    queryFn: getClasses,
  });
}

export function useClassDetail(classId: number) {
  return useQuery({
    queryKey: ['teacher', 'classes', classId],
    queryFn: () => getClassDetail(classId),
    enabled: !!classId,
  });
}

export function useClassOverview(classId: number) {
  return useQuery({
    queryKey: ['teacher', 'classes', classId, 'overview'],
    queryFn: () => getClassOverview(classId),
    enabled: !!classId,
  });
}

// Student Progress
export function useStudentProgress(classId: number, studentId: number) {
  return useQuery({
    queryKey: ['teacher', 'classes', classId, 'students', studentId],
    queryFn: () => getStudentProgress(classId, studentId),
    enabled: !!classId && !!studentId,
  });
}

export function useMasteryHistory(studentId: number) {
  return useQuery({
    queryKey: ['teacher', 'students', studentId, 'mastery-history'],
    queryFn: () => getMasteryHistory(studentId),
    enabled: !!studentId,
  });
}

// Analytics
export function useAnalyticsSummary(classId?: number) {
  return useQuery({
    queryKey: ['teacher', 'analytics', 'summary', classId],
    queryFn: () => getAnalyticsSummary(classId),
  });
}

export function useStrugglingTopics(classId?: number) {
  return useQuery({
    queryKey: ['teacher', 'analytics', 'struggling-topics', classId],
    queryFn: () => getStrugglingTopics(classId),
  });
}

export function useMasteryTrends(period: 'weekly' | 'monthly' = 'weekly', classId?: number) {
  return useQuery({
    queryKey: ['teacher', 'analytics', 'mastery-trends', period, classId],
    queryFn: () => getMasteryTrends(period, classId),
  });
}

// Self-Assessment Analytics
export function useSelfAssessmentSummary(classId?: number) {
  return useQuery({
    queryKey: ['teacher', 'analytics', 'self-assessment-summary', classId],
    queryFn: () => getSelfAssessmentSummary(classId),
  });
}

export function useMetacognitiveAlerts(classId?: number) {
  return useQuery({
    queryKey: ['teacher', 'analytics', 'metacognitive-alerts', classId],
    queryFn: () => getMetacognitiveAlerts(classId),
  });
}

export function useStudentSelfAssessments(studentId: number) {
  return useQuery({
    queryKey: ['teacher', 'students', studentId, 'self-assessments'],
    queryFn: () => getStudentSelfAssessments(studentId),
    enabled: !!studentId,
  });
}

// Diagnostic Analytics
export function useDiagnosticResults(classId?: number) {
  return useQuery({
    queryKey: ['teacher', 'analytics', 'diagnostic-results', classId],
    queryFn: () => getDiagnosticResults(classId),
  });
}

export function useDiagnosticAttemptAnswers(attemptId: number | null) {
  return useQuery({
    queryKey: ['teacher', 'analytics', 'diagnostic-answers', attemptId],
    queryFn: () => getDiagnosticAttemptAnswers(attemptId!),
    enabled: !!attemptId,
  });
}
