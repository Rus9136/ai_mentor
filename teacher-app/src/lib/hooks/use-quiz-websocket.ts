'use client';

import { useEffect, useRef, useCallback, useState } from 'react';

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || 'wss://api.ai-mentor.kz/api/v1';

interface WsMessage {
  type: string;
  data: Record<string, unknown>;
}

interface UseTeacherQuizWebSocketReturn {
  connected: boolean;
  lastMessage: WsMessage | null;
  sendNextQuestion: () => void;
  sendFinishQuiz: () => void;
  sendGoToQuestion: (index: number) => void;
  sendQuickQuestion: (questionText: string, options: string[]) => void;
  sendEndQuickQuestion: () => void;
  error: string | null;
}

export function useTeacherQuizWebSocket(joinCode: string | null): UseTeacherQuizWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCount = useRef(0);
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WsMessage | null>(null);
  const [error, setError] = useState<string | null>(null);

  const connect = useCallback(() => {
    if (!joinCode) return;

    const token = localStorage.getItem('ai_mentor_teacher_access_token');
    if (!token) {
      setError('No auth token');
      return;
    }

    const url = `${WS_BASE}/ws/quiz/${joinCode}?token=${token}`;

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        setError(null);
        reconnectCount.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data) as WsMessage;
          setLastMessage(msg);
        } catch {
          // ignore
        }
      };

      ws.onclose = (event) => {
        setConnected(false);
        wsRef.current = null;
        if (event.code === 1000 || event.code >= 4000) return;
        if (reconnectCount.current < 3) {
          reconnectCount.current++;
          setTimeout(connect, Math.pow(2, reconnectCount.current) * 1000);
        } else {
          setError('Connection lost');
        }
      };

      ws.onerror = () => setError('Connection error');
    } catch {
      setError('Failed to connect');
    }
  }, [joinCode]);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) {
        wsRef.current.close(1000);
        wsRef.current = null;
      }
    };
  }, [connect]);

  const send = useCallback((data: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const sendNextQuestion = useCallback(() => send({ type: 'next_question' }), [send]);
  const sendFinishQuiz = useCallback(() => send({ type: 'finish_quiz' }), [send]);
  const sendGoToQuestion = useCallback(
    (index: number) => send({ type: 'go_to_question', data: { question_index: index } }),
    [send],
  );
  const sendQuickQuestion = useCallback(
    (questionText: string, options: string[]) =>
      send({ type: 'quick_question', data: { question_text: questionText, options } }),
    [send],
  );
  const sendEndQuickQuestion = useCallback(() => send({ type: 'end_quick_question' }), [send]);

  return { connected, lastMessage, sendNextQuestion, sendFinishQuiz, sendGoToQuestion, sendQuickQuestion, sendEndQuickQuestion, error };
}
