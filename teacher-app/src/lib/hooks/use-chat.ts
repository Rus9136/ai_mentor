import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  createChatSession,
  listChatSessions,
  getChatSession,
  sendChatMessage,
  deleteChatSession,
} from '@/lib/api/chat';
import type { ChatSessionCreate } from '@/types/chat';

export const chatKeys = {
  all: ['chat'] as const,
  sessions: () => [...chatKeys.all, 'sessions'] as const,
  session: (id: number) => [...chatKeys.all, 'session', id] as const,
};

export function useChatSessions(page = 1, pageSize = 50) {
  return useQuery({
    queryKey: [...chatKeys.sessions(), page, pageSize],
    queryFn: () => listChatSessions({ page, page_size: pageSize }),
  });
}

export function useChatSession(id: number) {
  return useQuery({
    queryKey: chatKeys.session(id),
    queryFn: () => getChatSession(id),
    enabled: id > 0,
  });
}

export function useCreateChatSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ChatSessionCreate) => createChatSession(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: chatKeys.sessions() });
    },
  });
}

export function useSendMessage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ sessionId, content }: { sessionId: number; content: string }) =>
      sendChatMessage(sessionId, content),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: chatKeys.session(variables.sessionId) });
      queryClient.invalidateQueries({ queryKey: chatKeys.sessions() });
    },
  });
}

export function useDeleteChatSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: number) => deleteChatSession(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: chatKeys.sessions() });
    },
  });
}
