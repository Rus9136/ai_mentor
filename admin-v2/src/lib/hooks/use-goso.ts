import { useQuery } from '@tanstack/react-query';
import { gosoApi } from '@/lib/api/goso';

// ==================== Query Keys ====================

export const gosoKeys = {
  all: ['goso'] as const,
  subjects: () => [...gosoKeys.all, 'subjects'] as const,
  subject: (id: number) => [...gosoKeys.subjects(), id] as const,
  frameworks: (subjectId?: number) =>
    [...gosoKeys.all, 'frameworks', { subjectId }] as const,
  framework: (id: number) => [...gosoKeys.all, 'framework', id] as const,
  sections: (frameworkId: number) =>
    [...gosoKeys.all, 'sections', { frameworkId }] as const,
  outcomes: (params?: {
    framework_id?: number;
    subsection_id?: number;
    grade?: number;
    search?: string;
  }) => [...gosoKeys.all, 'outcomes', params] as const,
  outcome: (id: number) => [...gosoKeys.all, 'outcome', id] as const,
};

// ==================== Subjects ====================

export function useSubjects() {
  return useQuery({
    queryKey: gosoKeys.subjects(),
    queryFn: () => gosoApi.getSubjects(),
  });
}

export function useSubject(id: number, enabled = true) {
  return useQuery({
    queryKey: gosoKeys.subject(id),
    queryFn: () => gosoApi.getSubject(id),
    enabled: enabled && id > 0,
  });
}

// ==================== Frameworks ====================

export function useFrameworks(subjectId?: number) {
  return useQuery({
    queryKey: gosoKeys.frameworks(subjectId),
    queryFn: () => gosoApi.getFrameworks(subjectId),
  });
}

export function useFramework(id: number, enabled = true) {
  return useQuery({
    queryKey: gosoKeys.framework(id),
    queryFn: () => gosoApi.getFramework(id),
    enabled: enabled && id > 0,
  });
}

// ==================== Sections ====================

export function useSections(frameworkId: number, enabled = true) {
  return useQuery({
    queryKey: gosoKeys.sections(frameworkId),
    queryFn: () => gosoApi.getSections(frameworkId),
    enabled: enabled && frameworkId > 0,
  });
}

// ==================== Learning Outcomes ====================

export function useOutcomes(params?: {
  framework_id?: number;
  subsection_id?: number;
  grade?: number;
  search?: string;
}) {
  return useQuery({
    queryKey: gosoKeys.outcomes(params),
    queryFn: () => gosoApi.getOutcomes(params),
  });
}

export function useOutcome(id: number, enabled = true) {
  return useQuery({
    queryKey: gosoKeys.outcome(id),
    queryFn: () => gosoApi.getOutcome(id),
    enabled: enabled && id > 0,
  });
}
