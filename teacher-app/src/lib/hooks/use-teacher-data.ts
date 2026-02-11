import { useQuery } from '@tanstack/react-query';
import {
  getDashboard,
  getClasses,
  getClassDetail,
  getClassOverview,
  getStudentProgress,
  getMasteryHistory,
  getStrugglingTopics,
  getMasteryTrends,
  getSelfAssessmentSummary,
  getMetacognitiveAlerts,
  getStudentSelfAssessments,
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
export function useStrugglingTopics() {
  return useQuery({
    queryKey: ['teacher', 'analytics', 'struggling-topics'],
    queryFn: getStrugglingTopics,
  });
}

export function useMasteryTrends(period: 'weekly' | 'monthly' = 'weekly') {
  return useQuery({
    queryKey: ['teacher', 'analytics', 'mastery-trends', period],
    queryFn: () => getMasteryTrends(period),
  });
}

// Self-Assessment Analytics
export function useSelfAssessmentSummary() {
  return useQuery({
    queryKey: ['teacher', 'analytics', 'self-assessment-summary'],
    queryFn: getSelfAssessmentSummary,
  });
}

export function useMetacognitiveAlerts() {
  return useQuery({
    queryKey: ['teacher', 'analytics', 'metacognitive-alerts'],
    queryFn: getMetacognitiveAlerts,
  });
}

export function useStudentSelfAssessments(studentId: number) {
  return useQuery({
    queryKey: ['teacher', 'students', studentId, 'self-assessments'],
    queryFn: () => getStudentSelfAssessments(studentId),
    enabled: !!studentId,
  });
}
