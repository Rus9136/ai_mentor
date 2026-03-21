'use client';

import { useState, useRef, useEffect } from 'react';
import { useLocale, useTranslations } from 'next-intl';
import {
  X,
  Lightbulb,
  Search,
  FileCheck,
  ListOrdered,
  Send,
  Loader2,
  Bot,
  User,
} from 'lucide-react';
import { useCodingAIStream, useCodingSession } from '@/lib/hooks/use-coding-chat';
import type { CodingAction } from '@/lib/api/coding-chat';
import type { ChallengeDetail } from '@/lib/api/coding';

interface CodingAIPanelProps {
  challenge: ChallengeDetail;
  code: string;
  error?: string;
  testResults?: string;
  onClose: () => void;
}

const ACTION_BUTTONS: { action: CodingAction; icon: typeof Lightbulb; labelKey: string }[] = [
  { action: 'hint', icon: Lightbulb, labelKey: 'hint' },
  { action: 'explain_error', icon: Search, labelKey: 'explainError' },
  { action: 'code_review', icon: FileCheck, labelKey: 'codeReview' },
  { action: 'step_by_step', icon: ListOrdered, labelKey: 'stepByStep' },
];

export function CodingAIPanel({ challenge, code, error, testResults, onClose }: CodingAIPanelProps) {
  const locale = useLocale();
  const t = useTranslations('codingAI');
  const language = locale === 'kk' ? 'kk' : 'ru';

  const [followUp, setFollowUp] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const {
    messages,
    streamingContent,
    isStreaming,
    session,
    sendAction,
    sendFollowUp,
    setMessages,
  } = useCodingAIStream(challenge.id, language);

  // Load existing session
  const { data: existingSession } = useCodingSession(challenge.id);

  useEffect(() => {
    if (existingSession?.messages && messages.length === 0) {
      setMessages(existingSession.messages);
    }
  }, [existingSession, messages.length, setMessages]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  const handleAction = async (action: CodingAction) => {
    if (isStreaming) return;
    if (action === 'explain_error' && !error) return;
    await sendAction(action, code, error, testResults);
  };

  const handleFollowUp = async () => {
    if (!followUp.trim() || isStreaming) return;
    const msg = followUp.trim();
    setFollowUp('');
    await sendFollowUp(msg, code, error);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleFollowUp();
    }
  };

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-[420px] bg-background border-l border-border shadow-xl z-50 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-muted/30">
        <div className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-primary" />
          <h3 className="font-semibold text-sm">{t('title')}</h3>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-md hover:bg-muted transition-colors"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-1.5 px-3 py-2 border-b border-border overflow-x-auto">
        {ACTION_BUTTONS.map(({ action, icon: Icon, labelKey }) => {
          const disabled = isStreaming || (action === 'explain_error' && !error);
          return (
            <button
              key={action}
              onClick={() => handleAction(action)}
              disabled={disabled}
              className="flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-medium whitespace-nowrap
                bg-muted hover:bg-muted/80 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              title={action === 'explain_error' && !error ? t('noError') : undefined}
            >
              <Icon className="h-3.5 w-3.5" />
              {t(labelKey)}
            </button>
          );
        })}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3 min-h-0">
        {messages.length === 0 && !isStreaming && (
          <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
            <Bot className="h-10 w-10 mb-3 opacity-30" />
            <p className="text-sm">{t('placeholder')}</p>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.role === 'assistant' && (
              <div className="flex-shrink-0 mt-1">
                <Bot className="h-4 w-4 text-primary" />
              </div>
            )}
            <div
              className={`rounded-lg px-3 py-2 text-sm max-w-[85%] ${
                msg.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted'
              }`}
            >
              {msg.role === 'assistant' ? (
                <div
                  className="prose prose-sm dark:prose-invert max-w-none [&_pre]:bg-gray-900 [&_pre]:text-gray-100 [&_pre]:p-2 [&_pre]:rounded [&_pre]:text-xs [&_pre]:overflow-x-auto [&_code]:text-xs [&_code]:bg-gray-200 [&_code]:dark:bg-gray-700 [&_code]:px-1 [&_code]:rounded [&_pre_code]:bg-transparent [&_pre_code]:p-0"
                  dangerouslySetInnerHTML={{ __html: formatMarkdown(msg.content) }}
                />
              ) : (
                <p className="whitespace-pre-wrap break-words text-xs">{truncateUserMessage(msg.content)}</p>
              )}
            </div>
            {msg.role === 'user' && (
              <div className="flex-shrink-0 mt-1">
                <User className="h-4 w-4 text-muted-foreground" />
              </div>
            )}
          </div>
        ))}

        {/* Streaming indicator */}
        {isStreaming && streamingContent && (
          <div className="flex gap-2 justify-start">
            <div className="flex-shrink-0 mt-1">
              <Bot className="h-4 w-4 text-primary" />
            </div>
            <div className="rounded-lg px-3 py-2 text-sm bg-muted max-w-[85%]">
              <div
                className="prose prose-sm dark:prose-invert max-w-none [&_pre]:bg-gray-900 [&_pre]:text-gray-100 [&_pre]:p-2 [&_pre]:rounded [&_pre]:text-xs [&_pre]:overflow-x-auto [&_code]:text-xs [&_code]:bg-gray-200 [&_code]:dark:bg-gray-700 [&_code]:px-1 [&_code]:rounded [&_pre_code]:bg-transparent [&_pre_code]:p-0"
                dangerouslySetInnerHTML={{ __html: formatMarkdown(streamingContent) }}
              />
            </div>
          </div>
        )}

        {isStreaming && !streamingContent && (
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="text-xs">{t('thinking')}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-border px-3 py-2">
        <div className="flex items-end gap-2">
          <textarea
            value={followUp}
            onChange={(e) => setFollowUp(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t('inputPlaceholder')}
            disabled={isStreaming || !session}
            rows={1}
            className="flex-1 resize-none rounded-lg border border-border bg-background px-3 py-2 text-sm
              focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50
              max-h-[80px] overflow-y-auto"
          />
          <button
            onClick={handleFollowUp}
            disabled={!followUp.trim() || isStreaming || !session}
            className="p-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90
              disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * Simple markdown to HTML for AI responses.
 */
function formatMarkdown(text: string): string {
  return text
    .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br/>')
    .replace(/^/, '<p>')
    .replace(/$/, '</p>');
}

/**
 * Truncate long auto-generated user messages for display.
 */
function truncateUserMessage(content: string): string {
  if (content.length <= 200) return content;
  // Find first meaningful line (skip code blocks)
  const lines = content.split('\n');
  const firstLine = lines[0] || content.slice(0, 100);
  return firstLine.length > 150 ? firstLine.slice(0, 150) + '...' : firstLine + '...';
}
