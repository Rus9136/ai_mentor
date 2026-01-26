'use client';

import { useState } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { cn } from '@/lib/utils';
import {
  MessageSquare,
  Trash2,
  ChevronRight,
  AlertCircle,
  Loader2,
  Plus,
} from 'lucide-react';
import { useChatSessions, useDeleteChatSession } from '@/lib/hooks/use-chat';
import type { ChatSession, SessionType } from '@/lib/api/chat';

interface ChatHistoryProps {
  sessionType?: SessionType;
  onSelectSession: (sessionId: number) => void;
  onNewChat: () => void;
}

export function ChatHistory({
  sessionType,
  onSelectSession,
  onNewChat,
}: ChatHistoryProps) {
  const t = useTranslations('chat');
  const locale = useLocale();
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);

  const { data: sessionsData, isLoading, error } = useChatSessions(sessionType);
  const deleteSessionMutation = useDeleteChatSession();

  const sessions = sessionsData?.items || [];

  const handleDelete = (sessionId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (deleteConfirmId === sessionId) {
      deleteSessionMutation.mutate(sessionId, {
        onSuccess: () => setDeleteConfirmId(null),
      });
    } else {
      setDeleteConfirmId(sessionId);
    }
  };

  // Timezone for Kazakhstan
  const TIMEZONE = 'Asia/Almaty';

  // Format time in Almaty timezone
  const formatDate = (dateString: string | null) => {
    if (!dateString) return '';

    // Parse the date - assume server returns UTC if no timezone specified
    let date = new Date(dateString);

    // If the date string doesn't have timezone info, treat it as UTC
    if (!dateString.includes('Z') && !dateString.includes('+')) {
      date = new Date(dateString + 'Z');
    }

    const now = new Date();

    // Calculate difference in milliseconds
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    const isKk = locale === 'kk';

    // Very recent - just now
    if (diffMins < 1) return isKk ? 'жаңа ғана' : 'только что';

    // Less than an hour - show minutes
    if (diffMins < 60) return isKk ? `${diffMins} мин бұрын` : `${diffMins} мин назад`;

    // Less than 24 hours - show hours
    if (diffHours < 24) return isKk ? `${diffHours} сағ бұрын` : `${diffHours} ч назад`;

    // Less than 7 days - show days
    if (diffDays < 7) return isKk ? `${diffDays} күн бұрын` : `${diffDays} дн назад`;

    // Older entries - show date in Almaty timezone
    return date.toLocaleDateString(isKk ? 'kk-KZ' : 'ru-RU', {
      day: 'numeric',
      month: 'short',
      timeZone: TIMEZONE,
    });
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <Loader2 className="w-8 h-8 text-success animate-spin mb-3" />
        <p className="text-gray-500">{t('loading')}</p>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-6 text-center">
        <AlertCircle className="w-12 h-12 text-red-400 mb-4" />
        <p className="text-gray-600">{t('error')}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* New Chat Button */}
      <div className="p-4 border-b">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-success text-white rounded-xl font-medium hover:bg-success/90 transition-colors"
        >
          <Plus className="w-5 h-5" />
          {t('newChat')}
        </button>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto">
        {sessions.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full p-6 text-center">
            <MessageSquare className="w-12 h-12 text-gray-300 mb-4" />
            <p className="text-gray-500">{t('noHistory')}</p>
          </div>
        ) : (
          <div className="divide-y">
            {sessions.map((session) => (
              <SessionCard
                key={session.id}
                session={session}
                isDeleting={deleteSessionMutation.isPending && deleteConfirmId === session.id}
                isConfirmingDelete={deleteConfirmId === session.id}
                formatDate={formatDate}
                onSelect={() => onSelectSession(session.id)}
                onDelete={(e) => handleDelete(session.id, e)}
                onCancelDelete={() => setDeleteConfirmId(null)}
                t={t}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

interface SessionCardProps {
  session: ChatSession;
  isDeleting: boolean;
  isConfirmingDelete: boolean;
  formatDate: (date: string | null) => string;
  onSelect: () => void;
  onDelete: (e: React.MouseEvent) => void;
  onCancelDelete: () => void;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  t: ReturnType<typeof useTranslations<any>>;
}

function SessionCard({
  session,
  isDeleting,
  isConfirmingDelete,
  formatDate,
  onSelect,
  onDelete,
  onCancelDelete,
  t,
}: SessionCardProps) {
  return (
    <div
      className={cn(
        'group flex items-center gap-3 p-4 hover:bg-gray-50 cursor-pointer transition-colors',
        isConfirmingDelete && 'bg-red-50 hover:bg-red-50'
      )}
      onClick={isConfirmingDelete ? undefined : onSelect}
    >
      {/* Icon */}
      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-success/20 flex items-center justify-center">
        <MessageSquare className="w-5 h-5 text-success" />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <h4 className="font-medium text-gray-900 truncate">{session.title}</h4>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <span>{t('messagesCount', { count: session.message_count })}</span>
          {session.last_message_at && (
            <>
              <span>·</span>
              <span>{formatDate(session.last_message_at)}</span>
            </>
          )}
        </div>
      </div>

      {/* Actions */}
      {isConfirmingDelete ? (
        <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
          <button
            onClick={onDelete}
            disabled={isDeleting}
            className="px-3 py-1.5 bg-red-500 text-white text-sm rounded-lg hover:bg-red-600 transition-colors disabled:opacity-50"
          >
            {isDeleting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              t('deleteChat')
            )}
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onCancelDelete();
            }}
            className="px-3 py-1.5 bg-gray-200 text-gray-700 text-sm rounded-lg hover:bg-gray-300 transition-colors"
          >
            {t('cancel')}
          </button>
        </div>
      ) : (
        <div className="flex items-center gap-2">
          <button
            onClick={onDelete}
            className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg opacity-0 group-hover:opacity-100 transition-all"
            title={t('deleteChat')}
          >
            <Trash2 className="w-4 h-4" />
          </button>
          <ChevronRight className="w-5 h-5 text-gray-400" />
        </div>
      )}
    </div>
  );
}
