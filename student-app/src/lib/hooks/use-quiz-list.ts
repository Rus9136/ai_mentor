import { useQuery } from '@tanstack/react-query';
import { getMyQuizzes } from '@/lib/api/quiz';

export function useMyQuizzes() {
  return useQuery({
    queryKey: ['quizzes', 'my'],
    queryFn: getMyQuizzes,
    staleTime: 30 * 1000,
    refetchInterval: 60 * 1000,
  });
}
