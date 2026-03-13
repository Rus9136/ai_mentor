import { apiClient, getAccessToken } from './client';
import type {
  ChatSession,
  ChatSessionDetail,
  ChatSessionListResponse,
  ChatSessionCreate,
  ChatResponse,
} from '@/types/chat';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://api.ai-mentor.kz';

export async function createChatSession(data: ChatSessionCreate): Promise<ChatSession> {
  const res = await apiClient.post('/teachers/chat/sessions', data);
  return res.data;
}

export async function listChatSessions(params?: {
  page?: number;
  page_size?: number;
}): Promise<ChatSessionListResponse> {
  const res = await apiClient.get('/teachers/chat/sessions', { params });
  return res.data;
}

export async function getChatSession(sessionId: number): Promise<ChatSessionDetail> {
  const res = await apiClient.get(`/teachers/chat/sessions/${sessionId}`);
  return res.data;
}

export async function sendChatMessage(sessionId: number, content: string): Promise<ChatResponse> {
  const res = await apiClient.post(`/teachers/chat/sessions/${sessionId}/messages`, { content });
  return res.data;
}

export async function deleteChatSession(sessionId: number): Promise<void> {
  await apiClient.delete(`/teachers/chat/sessions/${sessionId}`);
}

/**
 * Stream chat message via SSE.
 * Returns an async generator of SSE events.
 */
export async function* streamChatMessage(
  sessionId: number,
  content: string,
  model?: string
): AsyncGenerator<{ type: string; content?: string; message?: any; session?: any; citations?: any[]; error?: string }> {
  const token = getAccessToken();
  const url = `${API_BASE_URL}/api/v1/teachers/chat/sessions/${sessionId}/messages/stream`;

  const body: Record<string, string> = { content };
  if (model) body.model = model;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    yield { type: 'error', error: `HTTP ${response.status}` };
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    yield { type: 'error', error: 'No response body' };
    return;
  }

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6));
          yield data;
        } catch {
          // skip malformed JSON
        }
      }
    }
  }

  // Process remaining buffer
  if (buffer.startsWith('data: ')) {
    try {
      const data = JSON.parse(buffer.slice(6));
      yield data;
    } catch {
      // skip
    }
  }
}
