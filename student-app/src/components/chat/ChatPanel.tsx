'use client';

import { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { Sparkles, Loader2, History, ArrowLeft } from 'lucide-react';
import { useCreateChatSession } from '@/lib/hooks/use-chat';
import { ChatWindow } from './ChatWindow';
import { ChatHistory } from './ChatHistory';
import type { SessionType } from '@/lib/api/chat';

interface ChatPanelProps {
  sessionType: SessionType;
  chapterId?: number;
  paragraphId?: number;
  paragraphTitle?: string | null;
  paragraphNumber?: number;
  language?: string;
  /** Called when the user closes chat via the flow (e.g., after post_paragraph) */
  onFlowClose?: () => void;
  /** Send a prompt programmatically (from QuickPrompts) */
  initialPrompt?: string | null;
  onInitialPromptSent?: () => void;
}

export function ChatPanel({
  sessionType,
  chapterId,
  paragraphId,
  paragraphTitle,
  paragraphNumber,
  language = 'ru',
  initialPrompt,
  onInitialPromptSent,
}: ChatPanelProps) {
  const t = useTranslations('chat');
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [showHistory, setShowHistory] = useState(false);

  const createSessionMutation = useCreateChatSession();

  // Create new session
  const createNewSession = () => {
    createSessionMutation.mutate(
      {
        session_type: sessionType,
        chapter_id: chapterId ?? null,
        paragraph_id: paragraphId ?? null,
        test_id: null,
        language,
      },
      {
        onSuccess: (session) => {
          setSessionId(session.id);
          setShowHistory(false);
        },
        onError: (error) => {
          console.error('Failed to create chat session:', error);
        },
      }
    );
  };

  // Create session on mount
  useEffect(() => {
    if (!sessionId && !showHistory && !createSessionMutation.isPending) {
      createNewSession();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Reset session when paragraph changes
  useEffect(() => {
    setSessionId(null);
    setShowHistory(false);
  }, [paragraphId, sessionType]);

  // Handle initial prompt after session is ready
  useEffect(() => {
    if (initialPrompt && sessionId && onInitialPromptSent) {
      // The ChatWindow will handle sending the message
      onInitialPromptSent();
    }
  }, [initialPrompt, sessionId, onInitialPromptSent]);

  const handleSelectSession = (id: number) => {
    setSessionId(id);
    setShowHistory(false);
  };

  const handleNewChat = () => {
    setSessionId(null);
    createNewSession();
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="flex items-center gap-2.5 px-4 py-3 border-b border-[#EDE8E3] bg-[#FFF8F2] flex-shrink-0">
        {showHistory ? (
          <button
            onClick={() => setShowHistory(false)}
            className="w-[34px] h-[34px] rounded-[10px] bg-success/20 flex items-center justify-center hover:bg-success/30 transition-colors"
          >
            <ArrowLeft className="w-4 h-4 text-success" />
          </button>
        ) : (
          <div className="w-[34px] h-[34px] rounded-[10px] bg-gradient-to-br from-success to-success/80 flex items-center justify-center flex-shrink-0">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <div className="text-sm font-extrabold text-foreground">
            {showHistory ? t('history') : t('panelTitle')}
          </div>
          {!showHistory && paragraphTitle && (
            <div className="text-[11px] font-semibold text-[#A09080] truncate">
              §{paragraphNumber} · {paragraphTitle}
            </div>
          )}
        </div>
        <div className="flex items-center gap-1.5 ml-auto">
          {!showHistory && sessionId && (
            <button
              onClick={() => setShowHistory(true)}
              className="w-[30px] h-[30px] rounded-[8px] bg-muted flex items-center justify-center hover:bg-muted/80 transition-colors"
              title={t('history')}
            >
              <History className="w-3.5 h-3.5 text-muted-foreground" />
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 min-h-0">
        {showHistory ? (
          <ChatHistory
            sessionType={sessionType}
            onSelectSession={handleSelectSession}
            onNewChat={handleNewChat}
          />
        ) : createSessionMutation.isPending || !sessionId ? (
          <div className="flex flex-col items-center justify-center h-full">
            <Loader2 className="w-8 h-8 text-success animate-spin mb-3" />
            <p className="text-gray-500 text-sm">{t('creating')}</p>
          </div>
        ) : createSessionMutation.isError ? (
          <div className="flex flex-col items-center justify-center h-full p-6 text-center">
            <p className="text-red-500 mb-4">{t('error')}</p>
            <button
              onClick={() => {
                setSessionId(null);
                createSessionMutation.reset();
              }}
              className="px-4 py-2 bg-success text-white rounded-lg hover:bg-success/90 transition-colors text-sm"
            >
              {t('retry')}
            </button>
          </div>
        ) : (
          <ChatWindow sessionId={sessionId} />
        )}
      </div>
    </div>
  );
}
