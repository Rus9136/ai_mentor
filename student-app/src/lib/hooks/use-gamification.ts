import { useQuery } from '@tanstack/react-query';
import {
  getGamificationProfile,
  getAchievements,
  getRecentAchievements,
  getLeaderboard,
  getDailyQuests,
  getXpHistory,
} from '@/lib/api/gamification';

export const gamificationKeys = {
  all: ['gamification'] as const,
  profile: () => [...gamificationKeys.all, 'profile'] as const,
  achievements: () => [...gamificationKeys.all, 'achievements'] as const,
  recentAchievements: () => [...gamificationKeys.all, 'achievements', 'recent'] as const,
  leaderboard: (scope: string, classId?: number) =>
    [...gamificationKeys.all, 'leaderboard', scope, classId] as const,
  dailyQuests: () => [...gamificationKeys.all, 'daily-quests'] as const,
  xpHistory: (days?: number) => [...gamificationKeys.all, 'xp-history', days] as const,
};

export function useGamificationProfile() {
  return useQuery({
    queryKey: gamificationKeys.profile(),
    queryFn: getGamificationProfile,
    staleTime: 30_000,
  });
}

export function useAchievements() {
  return useQuery({
    queryKey: gamificationKeys.achievements(),
    queryFn: getAchievements,
  });
}

export function useRecentAchievements() {
  return useQuery({
    queryKey: gamificationKeys.recentAchievements(),
    queryFn: getRecentAchievements,
    refetchInterval: 30_000,
  });
}

export function useLeaderboard(scope: 'school' | 'class', classId?: number) {
  return useQuery({
    queryKey: gamificationKeys.leaderboard(scope, classId),
    queryFn: () => getLeaderboard(scope, classId),
  });
}

export function useDailyQuests() {
  return useQuery({
    queryKey: gamificationKeys.dailyQuests(),
    queryFn: getDailyQuests,
  });
}

export function useXpHistory(days?: number) {
  return useQuery({
    queryKey: gamificationKeys.xpHistory(days),
    queryFn: () => getXpHistory(days),
  });
}
