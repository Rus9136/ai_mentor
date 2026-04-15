import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  generatePresentation,
  savePresentation,
  listPresentations,
  getPresentation,
  updatePresentation,
  updatePresentationTheme,
  deletePresentation,
  getTemplates,
} from '@/lib/api/presentations';
import type { PresentationTemplate } from '@/lib/api/presentations';
import type {
  SlideThemeName,
  PresentationGenerateRequest,
  PresentationGenerateResponse,
  PresentationSaveRequest,
  PresentationFullResponse,
  PresentationListItem,
  PresentationUpdateRequest,
} from '@/types/presentation';

export function usePresentationTemplates() {
  return useQuery<PresentationTemplate[]>({
    queryKey: ['presentation-templates'],
    queryFn: getTemplates,
    staleTime: 1000 * 60 * 60, // 1 hour
  });
}

export function useGeneratePresentation() {
  return useMutation<
    PresentationGenerateResponse,
    Error,
    PresentationGenerateRequest
  >({
    mutationFn: generatePresentation,
  });
}

export function useSavePresentation() {
  const queryClient = useQueryClient();
  return useMutation<PresentationFullResponse, Error, PresentationSaveRequest>({
    mutationFn: savePresentation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['presentations'] });
    },
  });
}

export function usePresentations(skip = 0, limit = 20) {
  return useQuery<PresentationListItem[]>({
    queryKey: ['presentations', skip, limit],
    queryFn: () => listPresentations(skip, limit),
  });
}

export function usePresentation(id: number | null) {
  return useQuery<PresentationFullResponse>({
    queryKey: ['presentations', id],
    queryFn: () => getPresentation(id!),
    enabled: !!id,
  });
}

export function useUpdatePresentation() {
  const queryClient = useQueryClient();
  return useMutation<
    PresentationFullResponse,
    Error,
    { id: number; data: PresentationUpdateRequest }
  >({
    mutationFn: ({ id, data }) => updatePresentation(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['presentations', id] });
      queryClient.invalidateQueries({ queryKey: ['presentations'] });
    },
  });
}

export function useUpdatePresentationTheme(id: number | null) {
  const queryClient = useQueryClient();
  return useMutation<
    { id: number; context_data: Record<string, unknown>; updated_at: string },
    Error,
    SlideThemeName,
    { previous: PresentationFullResponse | undefined }
  >({
    mutationFn: (theme) => updatePresentationTheme(id!, theme),
    onMutate: async (newTheme) => {
      await queryClient.cancelQueries({ queryKey: ['presentations', id] });
      const previous = queryClient.getQueryData<PresentationFullResponse>([
        'presentations',
        id,
      ]);
      if (previous) {
        queryClient.setQueryData<PresentationFullResponse>(
          ['presentations', id],
          {
            ...previous,
            context_data: { ...previous.context_data, theme: newTheme },
          }
        );
      }
      return { previous };
    },
    onError: (_err, _theme, context) => {
      if (context?.previous) {
        queryClient.setQueryData(['presentations', id], context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['presentations', id] });
    },
  });
}

export function useDeletePresentation() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, number>({
    mutationFn: deletePresentation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['presentations'] });
    },
  });
}
