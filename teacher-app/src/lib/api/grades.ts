/**
 * API functions for school gradebook (journal).
 */
import { apiClient } from './client';
import type {
  GradeResponse,
  GradeCreate,
  GradeUpdate,
  GradeFilterParams,
  SubjectListItem,
} from '@/types/grade';

// Grades

export async function getClassGrades(
  classId: number,
  subjectId: number,
  params?: GradeFilterParams
): Promise<GradeResponse[]> {
  const response = await apiClient.get<GradeResponse[]>(
    `/teachers/grades/class/${classId}/subject/${subjectId}`,
    { params }
  );
  return response.data;
}

export async function createGrade(data: GradeCreate): Promise<GradeResponse> {
  const response = await apiClient.post<GradeResponse>('/teachers/grades', data);
  return response.data;
}

export async function updateGrade(
  gradeId: number,
  data: GradeUpdate
): Promise<GradeResponse> {
  const response = await apiClient.put<GradeResponse>(`/teachers/grades/${gradeId}`, data);
  return response.data;
}

export async function deleteGrade(gradeId: number): Promise<void> {
  await apiClient.delete(`/teachers/grades/${gradeId}`);
}

// Subjects

export async function getSubjects(): Promise<SubjectListItem[]> {
  const response = await apiClient.get<SubjectListItem[]>('/goso/subjects');
  return response.data;
}
