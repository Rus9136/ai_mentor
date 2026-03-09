import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { prerequisitesApi, type PrerequisiteCreate } from '@/lib/api/prerequisites';
import { toast } from 'sonner';

export const prerequisiteKeys = {
  all: ['prerequisites'] as const,
  lists: () => [...prerequisiteKeys.all, 'list'] as const,
  list: (paragraphId: number) =>
    [...prerequisiteKeys.lists(), { paragraphId }] as const,
  graphs: () => [...prerequisiteKeys.all, 'graph'] as const,
  graph: (textbookId: number) =>
    [...prerequisiteKeys.graphs(), { textbookId }] as const,
};

export function usePrerequisites(paragraphId: number, enabled = true) {
  return useQuery({
    queryKey: prerequisiteKeys.list(paragraphId),
    queryFn: () => prerequisitesApi.getList(paragraphId),
    enabled: enabled && paragraphId > 0,
  });
}

export function useCreatePrerequisite() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      paragraphId,
      data,
    }: {
      paragraphId: number;
      data: PrerequisiteCreate;
    }) => prerequisitesApi.create(paragraphId, data),
    onSuccess: (result) => {
      queryClient.invalidateQueries({
        queryKey: prerequisiteKeys.list(result.paragraph_id),
      });
      toast.success('Пререквизит добавлен');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка: ${error.message}`);
    },
  });
}

export function useDeletePrerequisite() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      paragraphId,
    }: {
      id: number;
      paragraphId: number;
    }) => prerequisitesApi.delete(id),
    onSuccess: (_, { paragraphId }) => {
      queryClient.invalidateQueries({
        queryKey: prerequisiteKeys.list(paragraphId),
      });
      toast.success('Пререквизит удалён');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка удаления: ${error.message}`);
    },
  });
}

export function useTextbookPrerequisiteGraph(textbookId: number, enabled = true) {
  return useQuery({
    queryKey: prerequisiteKeys.graph(textbookId),
    queryFn: () => prerequisitesApi.getTextbookGraph(textbookId),
    enabled: enabled && textbookId > 0,
  });
}
