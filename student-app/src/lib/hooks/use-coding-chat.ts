import { useState, useCallback, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  CodingChatMessage,
  CodingChatSession,
  CodingAction,
  StartCodingAIRequest,
  streamCodingAI,
  streamCodingFollowUp,
  getChallengeSession,
} from '../api/coding-chat';

interface UseCodingAIStreamReturn {
  messages: CodingChatMessage[];
  streamingContent: string;
  isStreaming: boolean;
  session: CodingChatSession | null;
  sendAction: (action: CodingAction, code: string, error?: string, testResults?: string) => Promise<void>;
  sendFollowUp: (content: string, code?: string, error?: string) => Promise<void>;
  setMessages: React.Dispatch<React.SetStateAction<CodingChatMessage[]>>;
}

export function useCodingAIStream(challengeId: number, language: string = 'ru'): UseCodingAIStreamReturn {
  const [messages, setMessages] = useState<CodingChatMessage[]>([]);
  const [streamingContent, setStreamingContent] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [session, setSession] = useState<CodingChatSession | null>(null);
  const streamingRef = useRef(false);

  const sendAction = useCallback(async (
    action: CodingAction,
    code: string,
    error?: string,
    testResults?: string,
  ) => {
    if (streamingRef.current) return;
    streamingRef.current = true;
    setIsStreaming(true);
    setStreamingContent('');

    const request: StartCodingAIRequest = {
      challenge_id: challengeId,
      action,
      code,
      error: error || undefined,
      test_results: testResults || undefined,
      language,
    };

    await streamCodingAI(request, {
      onUserMessage: (msg) => {
        setMessages((prev) => [...prev, msg]);
      },
      onDelta: (content) => {
        setStreamingContent((prev) => prev + content);
      },
      onComplete: (msg, sess) => {
        setStreamingContent('');
        setMessages((prev) => [...prev, msg]);
        setSession(sess);
        streamingRef.current = false;
        setIsStreaming(false);
      },
      onError: (err) => {
        console.error('Coding AI error:', err);
        streamingRef.current = false;
        setIsStreaming(false);
      },
    });
  }, [challengeId, language]);

  const sendFollowUp = useCallback(async (
    content: string,
    code?: string,
    error?: string,
  ) => {
    if (streamingRef.current || !session) return;
    streamingRef.current = true;
    setIsStreaming(true);
    setStreamingContent('');

    await streamCodingFollowUp(session.id, { content, code, error }, {
      onUserMessage: (msg) => {
        setMessages((prev) => [...prev, msg]);
      },
      onDelta: (delta) => {
        setStreamingContent((prev) => prev + delta);
      },
      onComplete: (msg, sess) => {
        setStreamingContent('');
        setMessages((prev) => [...prev, msg]);
        setSession(sess);
        streamingRef.current = false;
        setIsStreaming(false);
      },
      onError: (err) => {
        console.error('Coding AI follow-up error:', err);
        streamingRef.current = false;
        setIsStreaming(false);
      },
    });
  }, [session]);

  return {
    messages,
    streamingContent,
    isStreaming,
    session,
    sendAction,
    sendFollowUp,
    setMessages,
  };
}

export function useCodingSession(challengeId: number) {
  return useQuery({
    queryKey: ['coding-ai-session', challengeId],
    queryFn: () => getChallengeSession(challengeId),
    staleTime: 60_000,
  });
}
