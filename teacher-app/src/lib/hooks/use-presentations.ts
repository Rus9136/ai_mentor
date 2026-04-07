import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  generatePresentation,
  savePresentation,
  listPresentations,
  getPresentation,
  updatePresentation,
  deletePresentation,
} from '@/lib/api/presentations';
import type {
  PresentationGenerateRequest,
  PresentationGenerateResponse,
  PresentationSaveRequest,
  PresentationFullResponse,
  PresentationListItem,
  PresentationUpdateRequest,
} from '@/types/presentation';

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

export function useDeletePresentation() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, number>({
    mutationFn: deletePresentation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['presentations'] });
    },
  });
}
