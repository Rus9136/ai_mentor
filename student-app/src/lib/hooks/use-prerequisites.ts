import { useQuery } from '@tanstack/react-query';
import { checkPrerequisites } from '@/lib/api/prerequisites';

/**
 * Check prerequisites for a paragraph.
 * Only fetches when paragraphId is provided.
 */
export function usePrerequisiteCheck(paragraphId: number | undefined) {
  return useQuery({
    queryKey: ['prerequisites', paragraphId],
    queryFn: () => checkPrerequisites(paragraphId!),
    enabled: !!paragraphId,
    staleTime: 5 * 60 * 1000,
  });
}
