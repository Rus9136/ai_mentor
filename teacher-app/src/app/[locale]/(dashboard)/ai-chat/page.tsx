'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import {
  Plus,
  Send,
  Trash2,
  Loader2,
  MessageSquare,
  BookOpen,
  X,
  Copy,
  Check,
  Sparkles,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { ContentSelector, type ContentSelection } from '@/components/homework/ContentSelector';
import {
  useChatSessions,
  useCreateChatSession,
  useDeleteChatSession,
} from '@/lib/hooks/use-chat';
import { getChatSession } from '@/lib/api/chat';
import { streamChatMessage } from '@/lib/api/chat';
import type { ChatMessage, ChatSession } from '@/types/chat';
import { cn } from '@/lib/utils';
import { MarkdownContent } from '@/components/chat/MarkdownContent';

export default function AIChatPage() {
  const t = useTranslations('aiChat');
  const tNav = useTranslations('navigation');

  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [showNewChat, setShowNewChat] = useState(false);
  const [contentSelection, setContentSelection] = useState<ContentSelection>({});
  const [loadingSession, setLoadingSession] = useState(false);
  const [sessionContext, setSessionContext] = useState<string>('');
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [copiedId, setCopiedId] = useState<number | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const { data: sessionsData, isLoading: sessionsLoading } = useChatSessions();
  const createSession = useCreateChatSession();
  const deleteSession = useDeleteChatSession();

  const sessions = sessionsData?.items || [];

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  // Load session messages when active session changes
  const loadSession = useCallback(async (sessionId: number) => {
    setLoadingSession(true);
    try {
      const detail = await getChatSession(sessionId);
      setMessages(detail.messages);
      // Build context label
      setSessionContext(detail.title || '');
    } catch {
      // ignore
    } finally {
      setLoadingSession(false);
    }
  }, []);

  useEffect(() => {
    if (activeSessionId && activeSessionId > 0) {
      loadSession(activeSessionId);
    }
  }, [activeSessionId, loadSession]);

  const handleCreateSession = async () => {
    if (!contentSelection.paragraphId || !contentSelection.chapterId) return;

    const title = contentSelection.paragraphTitle
      ? `${contentSelection.textbookTitle} - §${contentSelection.paragraphNumber}. ${contentSelection.paragraphTitle}`
      : undefined;

    try {
      const session = await createSession.mutateAsync({
        paragraph_id: contentSelection.paragraphId,
        chapter_id: contentSelection.chapterId,
        title,
      });
      setActiveSessionId(session.id);
      setMessages([]);
      setShowNewChat(false);
      setContentSelection({});
      setMobileSidebarOpen(false);
    } catch {
      // ignore
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim() || !activeSessionId || isStreaming) return;

    const userContent = input.trim();
    setInput('');
    setIsStreaming(true);
    setStreamingContent('');

    // Optimistically add user message
    const tempUserMsg: ChatMessage = {
      id: Date.now(),
      role: 'user',
      content: userContent,
      citations: null,
      tokens_used: null,
      model_used: null,
      processing_time_ms: null,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      let fullContent = '';
      let finalAssistantMessage: ChatMessage | null = null;
      let finalSession: ChatSession | null = null;

      for await (const event of streamChatMessage(activeSessionId, userContent)) {
        switch (event.type) {
          case 'user_message':
            // Replace temp message with real one
            if (event.message) {
              setMessages((prev) =>
                prev.map((m) => (m.id === tempUserMsg.id ? event.message! : m))
              );
            }
            break;
          case 'delta':
            if (event.content) {
              fullContent += event.content;
              setStreamingContent(fullContent);
            }
            break;
          case 'done':
            if (event.message) {
              finalAssistantMessage = event.message;
            }
            if (event.session) {
              finalSession = event.session;
            }
            break;
          case 'error':
            fullContent = event.error || 'Error';
            setStreamingContent(fullContent);
            break;
        }
      }

      // Add final assistant message
      if (finalAssistantMessage) {
        setMessages((prev) => [...prev, finalAssistantMessage!]);
      } else if (fullContent) {
        // Fallback if no done event
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now() + 1,
            role: 'assistant' as const,
            content: fullContent,
            citations: null,
            tokens_used: null,
            model_used: null,
            processing_time_ms: null,
            created_at: new Date().toISOString(),
          },
        ]);
      }

      // Update session title in sidebar if changed
      if (finalSession?.title) {
        setSessionContext(finalSession.title);
      }
    } catch {
      // Error handled by stream
    } finally {
      setIsStreaming(false);
      setStreamingContent('');
    }
  };

  const handleDeleteSession = async (sessionId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await deleteSession.mutateAsync(sessionId);
      if (activeSessionId === sessionId) {
        setActiveSessionId(null);
        setMessages([]);
      }
    } catch {
      // ignore
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSelectSession = (session: ChatSession) => {
    setActiveSessionId(session.id);
    setMobileSidebarOpen(false);
  };

  const handleCopy = async (content: string, msgId: number) => {
    await navigator.clipboard.writeText(content);
    setCopiedId(msgId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="flex h-[calc(100vh-7rem)] gap-4 lg:h-[calc(100vh-5rem)]">
      {/* Mobile sidebar toggle */}
      <Button
        variant="outline"
        size="sm"
        className="absolute left-6 top-[5.5rem] z-30 lg:hidden"
        onClick={() => setMobileSidebarOpen(!mobileSidebarOpen)}
      >
        <MessageSquare className="mr-1 h-4 w-4" />
        {t('title')}
      </Button>

      {/* Left Panel - Sessions List */}
      {mobileSidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}
      <Card
        className={cn(
          'flex w-72 flex-shrink-0 flex-col overflow-hidden',
          // Mobile: overlay
          'fixed inset-y-0 left-0 z-40 translate-x-0 transition-transform lg:relative lg:translate-x-0',
          !mobileSidebarOpen && 'max-lg:-translate-x-full'
        )}
      >
        <div className="flex items-center justify-between border-b p-3">
          <h2 className="text-sm font-semibold">{t('title')}</h2>
          <div className="flex items-center gap-1">
            <Button size="sm" variant="ghost" onClick={() => setShowNewChat(true)}>
              <Plus className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className="lg:hidden"
              onClick={() => setMobileSidebarOpen(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {sessionsLoading ? (
            <div className="flex items-center justify-center p-8">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : sessions.length === 0 ? (
            <div className="flex flex-col items-center gap-2 p-8 text-center text-sm text-muted-foreground">
              <MessageSquare className="h-8 w-8" />
              <p>{t('noSessions')}</p>
              <Button size="sm" onClick={() => setShowNewChat(true)}>
                <Plus className="mr-1 h-3 w-3" />
                {t('newChat')}
              </Button>
            </div>
          ) : (
            <div className="space-y-0.5 p-1">
              {sessions.map((session) => (
                <button
                  key={session.id}
                  onClick={() => handleSelectSession(session)}
                  className={cn(
                    'group flex w-full items-start gap-2 rounded-lg px-3 py-2 text-left text-sm transition-colors hover:bg-muted',
                    activeSessionId === session.id && 'bg-muted'
                  )}
                >
                  <MessageSquare className="mt-0.5 h-4 w-4 flex-shrink-0 text-muted-foreground" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium">{session.title || t('newChat')}</p>
                    <p className="truncate text-xs text-muted-foreground">
                      {session.message_count} {t('messages') || 'сообщ.'}
                    </p>
                  </div>
                  <button
                    onClick={(e) => handleDeleteSession(session.id, e)}
                    className="hidden flex-shrink-0 rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive group-hover:block"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </button>
              ))}
            </div>
          )}
        </div>
      </Card>

      {/* Right Panel - Chat Area */}
      <Card className="mt-10 flex flex-1 flex-col overflow-hidden lg:mt-0">
        {!activeSessionId ? (
          /* Empty state */
          <div className="flex flex-1 flex-col items-center justify-center gap-4 p-8 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
              <MessageSquare className="h-8 w-8 text-primary" />
            </div>
            <div>
              <h3 className="text-lg font-semibold">{t('title')}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{t('selectContent')}</p>
            </div>
            <Button onClick={() => setShowNewChat(true)}>
              <Plus className="mr-2 h-4 w-4" />
              {t('newChat')}
            </Button>
          </div>
        ) : (
          <>
            {/* Session header */}
            {sessionContext && (
              <div className="flex items-center gap-2 border-b px-4 py-2">
                <BookOpen className="h-4 w-4 text-muted-foreground" />
                <span className="truncate text-sm text-muted-foreground">{sessionContext}</span>
              </div>
            )}

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4">
              {loadingSession ? (
                <div className="flex items-center justify-center p-8">
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                </div>
              ) : messages.length === 0 && !isStreaming ? (
                <div className="flex flex-1 flex-col items-center justify-center gap-6 p-8">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10">
                    <Sparkles className="h-6 w-6 text-primary" />
                  </div>
                  <p className="text-sm text-muted-foreground">{t('startChat')}</p>
                  <div className="grid w-full max-w-lg grid-cols-1 gap-2 sm:grid-cols-2">
                    {(['prompt1', 'prompt2', 'prompt3', 'prompt4'] as const).map((key) => (
                      <button
                        key={key}
                        onClick={() => {
                          setInput(t(key));
                          inputRef.current?.focus();
                        }}
                        className="rounded-xl border bg-card px-4 py-3 text-left text-sm text-foreground transition-colors hover:bg-muted"
                      >
                        {t(key)}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="mx-auto max-w-3xl space-y-4">
                  {messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={cn(
                        'group flex',
                        msg.role === 'user' ? 'justify-end' : 'justify-start'
                      )}
                    >
                      <div
                        className={cn(
                          'max-w-[85%] rounded-2xl px-4 py-3 text-sm',
                          msg.role === 'user'
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted'
                        )}
                      >
                        {msg.role === 'assistant' ? (
                          <MarkdownContent content={msg.content} />
                        ) : (
                          <div className="whitespace-pre-wrap break-words">{msg.content}</div>
                        )}
                        {msg.processing_time_ms && msg.role === 'assistant' && (
                          <div className="mt-1 text-xs opacity-60">
                            {(msg.processing_time_ms / 1000).toFixed(1)}s
                          </div>
                        )}
                      </div>
                      {msg.role === 'assistant' && (
                        <button
                          onClick={() => handleCopy(msg.content, msg.id)}
                          className="mt-1 self-start rounded-md p-1 text-muted-foreground opacity-0 transition-opacity hover:bg-muted hover:text-foreground group-hover:opacity-100"
                          title={copiedId === msg.id ? 'Скопировано!' : 'Копировать'}
                        >
                          {copiedId === msg.id ? (
                            <Check className="h-3.5 w-3.5 text-green-500" />
                          ) : (
                            <Copy className="h-3.5 w-3.5" />
                          )}
                        </button>
                      )}
                    </div>
                  ))}

                  {/* Streaming indicator */}
                  {isStreaming && (
                    <div className="flex justify-start">
                      <div className="max-w-[85%] rounded-2xl bg-muted px-4 py-3 text-sm">
                        {streamingContent ? (
                          <MarkdownContent content={streamingContent} />
                        ) : (
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <Loader2 className="h-4 w-4 animate-spin" />
                            {t('thinking')}
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>

            {/* Input area */}
            <div className="border-t p-4">
              <div className="mx-auto flex max-w-3xl gap-2">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={t('placeholder')}
                  rows={1}
                  className="flex-1 resize-none rounded-xl border bg-background px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  disabled={isStreaming}
                />
                <Button
                  size="icon"
                  onClick={handleSendMessage}
                  disabled={!input.trim() || isStreaming}
                  className="h-11 w-11 rounded-xl"
                >
                  {isStreaming ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
          </>
        )}
      </Card>

      {/* New Chat Dialog */}
      <Dialog open={showNewChat} onOpenChange={setShowNewChat}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t('selectContent')}</DialogTitle>
          </DialogHeader>

          <ContentSelector
            onSelect={setContentSelection}
            disabled={createSession.isPending}
          />

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setShowNewChat(false)}>
              {t('cancel') || 'Отмена'}
            </Button>
            <Button
              onClick={handleCreateSession}
              disabled={!contentSelection.paragraphId || createSession.isPending}
            >
              {createSession.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <MessageSquare className="mr-2 h-4 w-4" />
              )}
              {t('startChat')}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
