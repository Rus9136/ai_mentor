import { apiClient } from './client';

export interface LeaderboardEntry {
  rank: number;
  student_id: number;
  student_name: string;
  total_xp: number;
  level: number;
}

export interface LeaderboardResponse {
  entries: LeaderboardEntry[];
  total_students: number;
  scope: string;
}

export async function getClassLeaderboard(classId: number): Promise<LeaderboardResponse> {
  const response = await apiClient.get(`/teachers/gamification/class/${classId}/leaderboard`);
  return response.data;
}
