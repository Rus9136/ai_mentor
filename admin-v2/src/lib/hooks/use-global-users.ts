import { useQuery, keepPreviousData } from '@tanstack/react-query';
import { globalUsersApi, type UsersListParams } from '@/lib/api/users';

export const globalUserKeys = {
  all: ['global-users'] as const,
  lists: () => [...globalUserKeys.all, 'list'] as const,
  list: (params?: UsersListParams) => [...globalUserKeys.lists(), params] as const,
};

export function useGlobalUsers(params?: UsersListParams) {
  return useQuery({
    queryKey: globalUserKeys.list(params),
    queryFn: () => globalUsersApi.getList(params),
    placeholderData: keepPreviousData,
  });
}
