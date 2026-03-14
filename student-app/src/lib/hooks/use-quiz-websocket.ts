'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
import type { WsServerMessage } from '@/types/quiz';

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || 'wss://api.ai-mentor.kz/api/v1';
const MAX_RECONNECTS = 3;

interface UseQuizWebSocketReturn {
  connected: boolean;
  lastMessage: WsServerMessage | null;
  send: (data: Record<string, unknown>) => void;
  error: string | null;
}

export function useQuizWebSocket(joinCode: string | null): UseQuizWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCount = useRef(0);
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WsServerMessage | null>(null);
  const [error, setError] = useState<string | null>(null);

  const connect = useCallback(() => {
    if (!joinCode) return;

    const token = localStorage.getItem('ai_mentor_access_token');
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
          const msg = JSON.parse(event.data) as WsServerMessage;
          setLastMessage(msg);
        } catch {
          // ignore parse errors
        }
      };

      ws.onclose = (event) => {
        setConnected(false);
        wsRef.current = null;

        // Don't reconnect on intentional close or auth failure
        if (event.code === 1000 || event.code >= 4000) return;

        if (reconnectCount.current < MAX_RECONNECTS) {
          reconnectCount.current++;
          const delay = Math.pow(2, reconnectCount.current) * 1000;
          setTimeout(connect, delay);
        } else {
          setError('Connection lost');
        }
      };

      ws.onerror = () => {
        setError('Connection error');
      };
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
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  return { connected, lastMessage, send, error };
}
