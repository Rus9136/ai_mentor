import { apiClient } from './client';

// =============================================================================
// Types
// =============================================================================

export type SessionType = 'reading_help' | 'post_paragraph' | 'test_help' | 'general_tutor';

export interface Citation {
  paragraph_id: number;
  paragraph_title: string;
  chapter_title: string;
  chunk_text: string;
  relevance_score: number;
}

export interface ChatMessage {
  id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  citations: Citation[] | null;
  tokens_used: number | null;
  model_used: string | null;
  processing_time_ms: number | null;
  created_at: string;
}

export interface ChatSession {
  id: number;
  session_type: SessionType;
  chapter_id: number | null;
  paragraph_id: number | null;
  test_id: number | null;
  title: string;
  mastery_level: 'A' | 'B' | 'C' | null;
  language: string;
  message_count: number;
  total_tokens_used: number;
  last_message_at: string | null;
  created_at: string;
}

export interface ChatSessionDetail extends ChatSession {
  messages: ChatMessage[];
}

export interface CreateSessionRequest {
  session_type: SessionType;
  chapter_id?: number | null;
  paragraph_id?: number | null;
  test_id?: number | null;
  title?: string;
  language?: string;
}

export interface SendMessageRequest {
  content: string;
}

export interface ChatResponse {
  user_message: ChatMessage;
  assistant_message: ChatMessage;
  session: {
    id: number;
    message_count: number;
    total_tokens_used: number;
    last_message_at: string;
  };
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// =============================================================================
// Streaming Types
// =============================================================================

export interface StreamUserMessageEvent {
  type: 'user_message';
  message: ChatMessage;
}

export interface StreamDeltaEvent {
  type: 'delta';
  content: string;
}

export interface StreamDoneEvent {
  type: 'done';
  message: ChatMessage;
  session: {
    id: number;
    message_count: number;
    total_tokens_used: number;
    last_message_at: string;
  };
  citations: Citation[];
}

export interface StreamErrorEvent {
  type: 'error';
  error: string;
}

export type StreamEvent = StreamUserMessageEvent | StreamDeltaEvent | StreamDoneEvent | StreamErrorEvent;

// =============================================================================
// API Functions
// =============================================================================

/**
 * Create a new chat session
 */
export async function createChatSession(data: CreateSessionRequest): Promise<ChatSession> {
  const response = await apiClient.post<ChatSession>('/chat/sessions', data);
  return response.data;
}

/**
 * Get a chat session with messages
 */
export async function getChatSession(sessionId: number): Promise<ChatSessionDetail> {
  const response = await apiClient.get<ChatSessionDetail>(`/chat/sessions/${sessionId}`);
  return response.data;
}

/**
 * Send a message in a chat session
 */
export async function sendChatMessage(
  sessionId: number,
  content: string
): Promise<ChatResponse> {
  const response = await apiClient.post<ChatResponse>(
    `/chat/sessions/${sessionId}/messages`,
    { content }
  );
  return response.data;
}

/**
 * Get list of chat sessions
 */
export async function getChatSessions(params?: {
  session_type?: SessionType;
  page?: number;
  page_size?: number;
}): Promise<PaginatedResponse<ChatSession>> {
  const response = await apiClient.get<PaginatedResponse<ChatSession>>('/chat/sessions', {
    params,
  });
  return response.data;
}

/**
 * Delete a chat session
 */
export async function deleteChatSession(sessionId: number): Promise<void> {
  await apiClient.delete(`/chat/sessions/${sessionId}`);
}

/**
 * Stream a chat message response via Server-Sent Events
 */
export async function streamChatMessage(
  sessionId: number,
  content: string,
  callbacks: {
    onUserMessage?: (message: ChatMessage) => void;
    onDelta?: (content: string) => void;
    onComplete?: (message: ChatMessage, session: StreamDoneEvent['session'], citations: Citation[]) => void;
    onError?: (error: string) => void;
  }
): Promise<void> {
  const baseURL = process.env.NEXT_PUBLIC_API_URL || '';
  const token = localStorage.getItem('access_token');

  const response = await fetch(`${baseURL}/chat/sessions/${sessionId}/messages/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : '',
    },
    body: JSON.stringify({ content }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    callbacks.onError?.(`HTTP error: ${response.status} - ${errorText}`);
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    callbacks.onError?.('No response body');
    return;
  }

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Process complete SSE events
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;

        const dataStr = line.slice(6); // Remove "data: " prefix
        if (!dataStr) continue;

        try {
          const event = JSON.parse(dataStr) as StreamEvent;

          switch (event.type) {
            case 'user_message':
              callbacks.onUserMessage?.(event.message);
              break;
            case 'delta':
              callbacks.onDelta?.(event.content);
              break;
            case 'done':
              callbacks.onComplete?.(event.message, event.session, event.citations);
              break;
            case 'error':
              callbacks.onError?.(event.error);
              break;
          }
        } catch {
          // Ignore parse errors for incomplete data
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
