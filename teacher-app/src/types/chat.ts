export interface ChatSession {
  id: number;
  session_type: string;
  paragraph_id: number | null;
  chapter_id: number | null;
  test_id: number | null;
  title: string | null;
  mastery_level: string | null;
  language: string;
  message_count: number;
  total_tokens_used: number;
  last_message_at: string | null;
  created_at: string;
  teacher_id: number | null;
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

export interface Citation {
  source: string;
  text: string;
  score: number;
}

export interface ChatSessionDetail extends ChatSession {
  messages: ChatMessage[];
}

export interface ChatSessionListResponse {
  items: ChatSession[];
  total: number;
  page: number;
  page_size: number;
}

export interface ChatSessionCreate {
  paragraph_id: number;
  chapter_id: number;
  title?: string;
  language?: string;
}

export interface ChatMessageCreate {
  content: string;
}

export interface ChatResponse {
  user_message: ChatMessage;
  assistant_message: ChatMessage;
  session: ChatSession;
}

export interface SSEEvent {
  type: 'user_message' | 'delta' | 'done' | 'error';
  content?: string;
  message?: ChatMessage;
  session?: ChatSession;
  citations?: Citation[];
  error?: string;
}
