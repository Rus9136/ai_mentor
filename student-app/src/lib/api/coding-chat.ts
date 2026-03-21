import { apiClient, getAccessToken, getRefreshToken, setTokens, clearTokens } from './client';

// =============================================================================
// Types
// =============================================================================

export type CodingAction = 'hint' | 'explain_error' | 'code_review' | 'step_by_step' | 'free_chat';

export interface CodingChatMessage {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  tokens_used: number | null;
  model_used: string | null;
  processing_time_ms: number | null;
  created_at: string;
}

export interface CodingChatSession {
  id: number;
  session_type: string;
  challenge_id: number | null;
  title: string | null;
  language: string;
  message_count: number;
  total_tokens_used: number;
  last_message_at: string | null;
  created_at: string;
}

export interface CodingChatSessionDetail extends CodingChatSession {
  messages: CodingChatMessage[];
}

export interface StartCodingAIRequest {
  challenge_id: number;
  action: CodingAction;
  code: string;
  error?: string;
  test_results?: string;
  language?: string;
}

export interface CodingChatMessageRequest {
  content: string;
  code?: string;
  error?: string;
}

// SSE event types
interface StreamDoneEvent {
  type: 'done';
  message: CodingChatMessage;
  session: CodingChatSession;
}

interface StreamCallbacks {
  onUserMessage?: (message: CodingChatMessage) => void;
  onDelta?: (content: string) => void;
  onComplete?: (message: CodingChatMessage, session: CodingChatSession) => void;
  onError?: (error: string) => void;
}

// =============================================================================
// Helper: Token refresh
// =============================================================================

async function ensureValidToken(): Promise<string | null> {
  const baseURL = process.env.NEXT_PUBLIC_API_URL || '';
  let token = getAccessToken();

  if (!token) {
    const refreshToken = getRefreshToken();
    if (!refreshToken) return null;

    try {
      const response = await fetch(`${baseURL}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (response.ok) {
        const data = await response.json();
        setTokens(data.access_token, data.refresh_token);
        token = data.access_token;
      } else {
        clearTokens();
        return null;
      }
    } catch {
      clearTokens();
      return null;
    }
  }

  return token;
}

// =============================================================================
// SSE Stream helper
// =============================================================================

async function streamSSE(
  url: string,
  body: object,
  callbacks: StreamCallbacks,
): Promise<void> {
  const baseURL = process.env.NEXT_PUBLIC_API_URL || '';
  let token = getAccessToken();

  const makeRequest = async (authToken: string | null) => {
    return fetch(`${baseURL}${url}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authToken ? `Bearer ${authToken}` : '',
      },
      body: JSON.stringify(body),
    });
  };

  let response = await makeRequest(token);

  if (response.status === 401 || response.status === 403) {
    const newToken = await ensureValidToken();
    if (newToken && newToken !== token) {
      response = await makeRequest(newToken);
    }
  }

  if (!response.ok) {
    if (response.status === 401 || response.status === 403) {
      clearTokens();
      window.location.href = '/ru/login';
      return;
    }
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

      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const dataStr = line.slice(6);
        if (!dataStr) continue;

        try {
          const event = JSON.parse(dataStr);

          switch (event.type) {
            case 'user_message':
              callbacks.onUserMessage?.(event.message);
              break;
            case 'delta':
              callbacks.onDelta?.(event.content);
              break;
            case 'done':
              callbacks.onComplete?.(event.message, event.session);
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

// =============================================================================
// API Functions
// =============================================================================

export async function streamCodingAI(
  request: StartCodingAIRequest,
  callbacks: StreamCallbacks,
): Promise<void> {
  return streamSSE('/students/coding/ai/start', request, callbacks);
}

export async function streamCodingFollowUp(
  sessionId: number,
  request: CodingChatMessageRequest,
  callbacks: StreamCallbacks,
): Promise<void> {
  return streamSSE(`/students/coding/ai/sessions/${sessionId}/messages/stream`, request, callbacks);
}

export async function getCodingSession(sessionId: number): Promise<CodingChatSessionDetail> {
  const response = await apiClient.get<CodingChatSessionDetail>(
    `/students/coding/ai/sessions/${sessionId}`
  );
  return response.data;
}

export async function getChallengeSession(challengeId: number): Promise<CodingChatSessionDetail | null> {
  const response = await apiClient.get<CodingChatSessionDetail | null>(
    `/students/coding/ai/challenge/${challengeId}/session`
  );
  return response.data;
}
