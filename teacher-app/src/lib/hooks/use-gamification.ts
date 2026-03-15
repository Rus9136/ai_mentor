import { useQuery } from '@tanstack/react-query';
import { getClassLeaderboard } from '@/lib/api/gamification';

export const gamificationKeys = {
  all: ['gamification'] as const,
  classLeaderboard: (classId: number) => [...gamificationKeys.all, 'class-leaderboard', classId] as const,
};

export function useClassLeaderboard(classId: number) {
  return useQuery({
    queryKey: gamificationKeys.classLeaderboard(classId),
    queryFn: () => getClassLeaderboard(classId),
    enabled: classId > 0,
  });
}
