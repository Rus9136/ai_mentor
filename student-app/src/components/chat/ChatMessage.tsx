'use client';

import { useTranslations } from 'next-intl';
import { cn } from '@/lib/utils';
import { User, Sparkles } from 'lucide-react';
import { ChatCitation } from './ChatCitation';
import type { ChatMessage as ChatMessageType } from '@/lib/api/chat';

interface ChatMessageProps {
  message: ChatMessageType;
  className?: string;
}

export function ChatMessage({ message, className }: ChatMessageProps) {
  const t = useTranslations('chat');
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';

  return (
    <div className={cn('flex gap-3', isUser && 'flex-row-reverse', className)}>
      {/* Avatar */}
      <div
        className={cn(
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
          isUser ? 'bg-amber-100' : 'bg-purple-100'
        )}
      >
        {isUser ? (
          <User className="w-4 h-4 text-amber-600" />
        ) : (
          <Sparkles className="w-4 h-4 text-purple-600" />
        )}
      </div>

      {/* Message content */}
      <div className={cn('flex-1 max-w-[80%]', isUser && 'flex flex-col items-end')}>
        <div
          className={cn(
            'px-4 py-2 rounded-2xl',
            isUser
              ? 'bg-amber-500 text-white rounded-tr-sm'
              : 'bg-gray-100 text-gray-900 rounded-tl-sm'
          )}
        >
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        </div>

        {/* Citations */}
        {isAssistant && message.citations && message.citations.length > 0 && (
          <div className="mt-2 space-y-2 w-full">
            <p className="text-xs text-gray-500 font-medium">
              {t('citations')}:
            </p>
            {message.citations.map((citation, index) => (
              <ChatCitation key={index} citation={citation} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
