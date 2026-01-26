import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  createChatSession,
  getChatSession,
  sendChatMessage,
  getChatSessions,
  deleteChatSession,
  streamChatMessage,
  CreateSessionRequest,
  ChatSession,
  ChatSessionDetail,
  ChatResponse,
  ChatMessage,
  Citation,
  SessionType,
  StreamDoneEvent,
} from '@/lib/api/chat';

// =============================================================================
// Query Keys Factory
// =============================================================================

export const chatKeys = {
  all: ['chat'] as const,
  sessions: () => [...chatKeys.all, 'sessions'] as const,
  sessionsList: (sessionType?: SessionType) => [...chatKeys.sessions(), sessionType] as const,
  session: (sessionId: number) => [...chatKeys.all, 'session', sessionId] as const,
};

// =============================================================================
// Hooks
// =============================================================================

/**
 * Hook to create a new chat session
 */
export function useCreateChatSession() {
  const queryClient = useQueryClient();

  return useMutation<ChatSession, Error, CreateSessionRequest>({
    mutationFn: (data) => createChatSession(data),
    onSuccess: (data) => {
      // Cache the new session
      queryClient.setQueryData(chatKeys.session(data.id), {
        ...data,
        messages: [],
      } as ChatSessionDetail);
      // Invalidate sessions list
      queryClient.invalidateQueries({ queryKey: chatKeys.sessions() });
    },
  });
}

/**
 * Hook to get a chat session with messages
 */
export function useChatSession(sessionId: number | undefined) {
  return useQuery<ChatSessionDetail, Error>({
    queryKey: chatKeys.session(sessionId!),
    queryFn: () => getChatSession(sessionId!),
    enabled: !!sessionId,
  });
}

/**
 * Hook to send a message in a chat session
 */
export function useSendMessage(sessionId: number) {
  const queryClient = useQueryClient();

  return useMutation<ChatResponse, Error, string>({
    mutationFn: (content) => sendChatMessage(sessionId, content),
    onSuccess: (data) => {
      // Update cached session with new messages
      queryClient.setQueryData<ChatSessionDetail>(
        chatKeys.session(sessionId),
        (oldData) => {
          if (!oldData) return oldData;
          return {
            ...oldData,
            messages: [...oldData.messages, data.user_message, data.assistant_message],
            message_count: data.session.message_count,
            total_tokens_used: data.session.total_tokens_used,
            last_message_at: data.session.last_message_at,
          };
        }
      );
      // Invalidate sessions list to update last_message_at
      queryClient.invalidateQueries({ queryKey: chatKeys.sessions() });
    },
  });
}

/**
 * Hook to get list of chat sessions
 */
export function useChatSessions(sessionType?: SessionType) {
  return useQuery({
    queryKey: chatKeys.sessionsList(sessionType),
    queryFn: () => getChatSessions({ session_type: sessionType, page_size: 50 }),
  });
}

/**
 * Hook to delete a chat session
 */
export function useDeleteChatSession() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, number>({
    mutationFn: (sessionId) => deleteChatSession(sessionId),
    onSuccess: (_, sessionId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: chatKeys.session(sessionId) });
      // Invalidate sessions list
      queryClient.invalidateQueries({ queryKey: chatKeys.sessions() });
    },
  });
}

/**
 * Hook for streaming chat messages
 */
export function useStreamMessage(sessionId: number) {
  const queryClient = useQueryClient();
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [error, setError] = useState<string | null>(null);

  const sendStreamingMessage = useCallback(
    async (content: string) => {
      setIsStreaming(true);
      setStreamingContent('');
      setError(null);

      try {
        await streamChatMessage(sessionId, content, {
          onUserMessage: (message: ChatMessage) => {
            // Add user message to cache immediately
            queryClient.setQueryData<ChatSessionDetail>(
              chatKeys.session(sessionId),
              (oldData) => {
                if (!oldData) return oldData;
                return {
                  ...oldData,
                  messages: [...oldData.messages, message],
                };
              }
            );
          },
          onDelta: (delta: string) => {
            setStreamingContent((prev) => prev + delta);
          },
          onComplete: (
            message: ChatMessage,
            session: StreamDoneEvent['session'],
            citations: Citation[]
          ) => {
            // Update cache with final assistant message
            queryClient.setQueryData<ChatSessionDetail>(
              chatKeys.session(sessionId),
              (oldData) => {
                if (!oldData) return oldData;
                return {
                  ...oldData,
                  messages: [...oldData.messages, { ...message, citations }],
                  message_count: session.message_count,
                  total_tokens_used: session.total_tokens_used,
                  last_message_at: session.last_message_at,
                };
              }
            );
            setStreamingContent('');
            setIsStreaming(false);
            // Invalidate sessions list
            queryClient.invalidateQueries({ queryKey: chatKeys.sessions() });
          },
          onError: (errorMsg: string) => {
            setError(errorMsg);
            setIsStreaming(false);
            setStreamingContent('');
          },
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
        setIsStreaming(false);
        setStreamingContent('');
      }
    },
    [sessionId, queryClient]
  );

  const reset = useCallback(() => {
    setIsStreaming(false);
    setStreamingContent('');
    setError(null);
  }, []);

  return {
    sendStreamingMessage,
    isStreaming,
    streamingContent,
    error,
    reset,
  };
}
