import { apiClient } from './client';
import type { SchoolClass, SchoolClassCreate, SchoolClassUpdate, PaginatedResponse } from '@/types';

export const classesApi = {
  getList: async (): Promise<SchoolClass[]> => {
    const { data } = await apiClient.get<PaginatedResponse<SchoolClass>>('/admin/school/classes');
    return data.items;
  },

  getOne: async (id: number): Promise<SchoolClass> => {
    const { data } = await apiClient.get<SchoolClass>(`/admin/school/classes/${id}`);
    return data;
  },

  create: async (payload: SchoolClassCreate): Promise<SchoolClass> => {
    const { data } = await apiClient.post<SchoolClass>('/admin/school/classes', payload);
    return data;
  },

  update: async (id: number, payload: SchoolClassUpdate): Promise<SchoolClass> => {
    const { data } = await apiClient.put<SchoolClass>(`/admin/school/classes/${id}`, payload);
    return data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/admin/school/classes/${id}`);
  },

  // Students management
  addStudents: async (classId: number, studentIds: number[]): Promise<SchoolClass> => {
    const { data } = await apiClient.post<SchoolClass>(`/admin/school/classes/${classId}/students`, {
      student_ids: studentIds,
    });
    return data;
  },

  removeStudent: async (classId: number, studentId: number): Promise<SchoolClass> => {
    const { data } = await apiClient.delete<SchoolClass>(
      `/admin/school/classes/${classId}/students/${studentId}`
    );
    return data;
  },

  // Teachers management
  addTeachers: async (classId: number, teacherIds: number[]): Promise<SchoolClass> => {
    const { data } = await apiClient.post<SchoolClass>(`/admin/school/classes/${classId}/teachers`, {
      teacher_ids: teacherIds,
    });
    return data;
  },

  removeTeacher: async (classId: number, teacherId: number): Promise<SchoolClass> => {
    const { data } = await apiClient.delete<SchoolClass>(
      `/admin/school/classes/${classId}/teachers/${teacherId}`
    );
    return data;
  },
};
