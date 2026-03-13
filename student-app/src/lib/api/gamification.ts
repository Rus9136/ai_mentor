import { apiClient } from './client';
import type {
  GamificationProfile,
  StudentAchievement,
  Leaderboard,
  DailyQuest,
  XpHistoryEntry,
} from '@/types/gamification';

export async function getGamificationProfile(): Promise<GamificationProfile> {
  const response = await apiClient.get<GamificationProfile>('/students/gamification/profile');
  return response.data;
}

export async function getAchievements(): Promise<StudentAchievement[]> {
  const response = await apiClient.get<StudentAchievement[]>('/students/gamification/achievements');
  return response.data;
}

export async function getRecentAchievements(): Promise<StudentAchievement[]> {
  const response = await apiClient.get<StudentAchievement[]>('/students/gamification/achievements/recent');
  return response.data;
}

export async function getLeaderboard(
  scope: 'school' | 'class',
  classId?: number
): Promise<Leaderboard> {
  const response = await apiClient.get<Leaderboard>('/students/gamification/leaderboard', {
    params: { scope, class_id: classId },
  });
  return response.data;
}

export async function getDailyQuests(): Promise<DailyQuest[]> {
  const response = await apiClient.get<DailyQuest[]>('/students/gamification/daily-quests');
  return response.data;
}

export async function getXpHistory(days?: number): Promise<XpHistoryEntry[]> {
  const response = await apiClient.get<XpHistoryEntry[]>('/students/gamification/xp-history', {
    params: days ? { days } : undefined,
  });
  return response.data;
}
