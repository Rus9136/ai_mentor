'use client';

import { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { X, Sparkles, Loader2, History, ArrowLeft } from 'lucide-react';
import { useCreateChatSession } from '@/lib/hooks/use-chat';
import { ChatWindow } from './ChatWindow';
import { ChatHistory } from './ChatHistory';
import type { SessionType } from '@/lib/api/chat';

interface ChatModalProps {
  isOpen: boolean;
  onClose: () => void;
  sessionType: SessionType;
  chapterId?: number;
  paragraphId?: number;
  testId?: number;
  language?: string;
}

export function ChatModal({
  isOpen,
  onClose,
  sessionType,
  chapterId,
  paragraphId,
  testId,
  language = 'ru',
}: ChatModalProps) {
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
        test_id: testId ?? null,
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

  // Create session when modal opens (only if not showing history)
  useEffect(() => {
    if (isOpen && !sessionId && !showHistory && !createSessionMutation.isPending) {
      createNewSession();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, sessionId, showHistory]);

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setSessionId(null);
      setShowHistory(false);
    }
  }, [isOpen]);

  // Handle selecting session from history
  const handleSelectSession = (id: number) => {
    setSessionId(id);
    setShowHistory(false);
  };

  // Handle creating new chat from history
  const handleNewChat = () => {
    setSessionId(null);
    createNewSession();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-lg h-[85vh] max-h-[700px] bg-white rounded-2xl shadow-2xl mx-4 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex-shrink-0 flex items-center justify-between px-4 py-3 border-b bg-gradient-to-r from-purple-500 to-purple-600">
          <div className="flex items-center gap-3">
            {showHistory ? (
              <button
                onClick={() => setShowHistory(false)}
                className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center hover:bg-white/30 transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-white" />
              </button>
            ) : (
              <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
            )}
            <div>
              <h2 className="font-bold text-white">
                {showHistory ? t('history') : t('title')}
              </h2>
              <p className="text-xs text-purple-100">
                {showHistory ? t('selectChat') : t('subtitle')}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {!showHistory && sessionId && (
              <button
                onClick={() => setShowHistory(true)}
                className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center hover:bg-white/30 transition-colors"
                title={t('history')}
              >
                <History className="w-4 h-4 text-white" />
              </button>
            )}
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center hover:bg-white/30 transition-colors"
            >
              <X className="w-4 h-4 text-white" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-h-0 bg-gray-50">
          {showHistory ? (
            <ChatHistory
              sessionType={sessionType}
              onSelectSession={handleSelectSession}
              onNewChat={handleNewChat}
            />
          ) : createSessionMutation.isPending || !sessionId ? (
            <div className="flex flex-col items-center justify-center h-full">
              <Loader2 className="w-8 h-8 text-purple-500 animate-spin mb-3" />
              <p className="text-gray-500">{t('creating')}</p>
            </div>
          ) : createSessionMutation.isError ? (
            <div className="flex flex-col items-center justify-center h-full p-6 text-center">
              <p className="text-red-500 mb-4">{t('error')}</p>
              <button
                onClick={() => {
                  setSessionId(null);
                  createSessionMutation.reset();
                }}
                className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors"
              >
                {t('retry')}
              </button>
            </div>
          ) : (
            <ChatWindow sessionId={sessionId} />
          )}
        </div>
      </div>
    </div>
  );
}
