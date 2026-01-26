'use client';

import { useEffect, useRef } from 'react';
import { useTranslations } from 'next-intl';
import { Sparkles, AlertCircle } from 'lucide-react';
import { useChatSession, useSendMessage } from '@/lib/hooks/use-chat';
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
  const sendMessageMutation = useSendMessage(sessionId);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [session?.messages]);

  const handleSend = (content: string) => {
    sendMessageMutation.mutate(content);
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
  const hasMessages = messages.length > 0;

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {!hasMessages ? (
          // Empty state
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 rounded-full bg-purple-100 flex items-center justify-center mb-4">
              <Sparkles className="w-8 h-8 text-purple-500" />
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

            {/* Typing indicator when sending */}
            {sendMessageMutation.isPending && (
              <div className="flex gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
                  <Sparkles className="w-4 h-4 text-purple-600" />
                </div>
                <TypingIndicator text={t('thinking')} />
              </div>
            )}

            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input area */}
      <ChatInput
        onSend={handleSend}
        isLoading={sendMessageMutation.isPending}
      />
    </div>
  );
}
