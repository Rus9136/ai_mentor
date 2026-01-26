'use client';

import { useEffect, useRef } from 'react';
import { useTranslations } from 'next-intl';
import { Sparkles, AlertCircle } from 'lucide-react';
import { useChatSession, useStreamMessage } from '@/lib/hooks/use-chat';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { TypingIndicator } from './TypingIndicator';

interface ChatWindowProps {
  sessionId: number;
}

export function ChatWindow({ sessionId }: ChatWindowProps) {
  const t = useTranslations('chat');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: session, isLoading: isLoadingSession, error } = useChatSession(sessionId);
  const { sendStreamingMessage, isStreaming, streamingContent, error: streamError } = useStreamMessage(sessionId);

  // Scroll to bottom when messages change or streaming content updates
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [session?.messages, streamingContent]);

  const handleSend = (content: string) => {
    sendStreamingMessage(content);
  };

  // Loading state
  if (isLoadingSession) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <TypingIndicator text={t('loading')} />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
        <AlertCircle className="w-12 h-12 text-red-400 mb-4" />
        <p className="text-gray-600">{t('error')}</p>
      </div>
    );
  }

  const messages = session?.messages || [];
  const hasMessages = messages.length > 0 || isStreaming;

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {!hasMessages ? (
          // Empty state
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 rounded-full bg-success/20 flex items-center justify-center mb-4">
              <Sparkles className="w-8 h-8 text-success" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {t('emptyTitle')}
            </h3>
            <p className="text-gray-500 max-w-xs">
              {t('emptyHint')}
            </p>
          </div>
        ) : (
          // Messages list
          <>
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}

            {/* Streaming response */}
            {isStreaming && streamingContent && (
              <div className="flex gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-success/20 flex items-center justify-center">
                  <Sparkles className="w-4 h-4 text-success" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="bg-gray-100 rounded-2xl rounded-tl-md px-4 py-3">
                    <p className="text-gray-800 whitespace-pre-wrap">
                      {streamingContent}
                      <span className="inline-block w-2 h-4 bg-success ml-0.5 animate-pulse" />
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Typing indicator when waiting for first token */}
            {isStreaming && !streamingContent && (
              <div className="flex gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-success/20 flex items-center justify-center">
                  <Sparkles className="w-4 h-4 text-success" />
                </div>
                <TypingIndicator text={t('thinking')} />
              </div>
            )}

            {/* Stream error */}
            {streamError && (
              <div className="flex gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-red-100 flex items-center justify-center">
                  <AlertCircle className="w-4 h-4 text-red-600" />
                </div>
                <div className="bg-red-50 rounded-2xl px-4 py-3">
                  <p className="text-red-600 text-sm">{streamError}</p>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input area */}
      <ChatInput
        onSend={handleSend}
        isLoading={isStreaming}
      />
    </div>
  );
}
