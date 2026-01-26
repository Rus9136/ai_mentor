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
