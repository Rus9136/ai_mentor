'use client';

import { useState, useRef, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { Send, Loader2, Zap, Brain } from 'lucide-react';

export type ChatMode = 'fast' | 'deep';

interface ChatInputProps {
  onSend: (message: string, mode: ChatMode) => void;
  isLoading?: boolean;
  disabled?: boolean;
  initialValue?: string | null;
  onInitialValueConsumed?: () => void;
}

export function ChatInput({ onSend, isLoading, disabled, initialValue, onInitialValueConsumed }: ChatInputProps) {
  const t = useTranslations('chat');
  const [input, setInput] = useState('');
  const [mode, setMode] = useState<ChatMode>('fast');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Pre-fill input from initialValue
  useEffect(() => {
    if (initialValue) {
      setInput(initialValue);
      onInitialValueConsumed?.();
      // Focus the textarea
      setTimeout(() => textareaRef.current?.focus(), 100);
    }
  }, [initialValue, onInitialValueConsumed]);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
    }
  }, [input]);

  const handleSubmit = () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading || disabled) return;
    onSend(trimmed, mode);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t bg-white">
      {/* Mode selector */}
      <div className="flex items-center gap-1.5 px-4 pt-3 pb-1">
        <button
          onClick={() => setMode('fast')}
          disabled={isLoading}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
            mode === 'fast'
              ? 'bg-success/15 text-success ring-1 ring-success/30'
              : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
          } disabled:opacity-50`}
        >
          <Zap className="w-3 h-3" />
          {t('modeFast')}
        </button>
        <button
          onClick={() => setMode('deep')}
          disabled={isLoading}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
            mode === 'deep'
              ? 'bg-violet-100 text-violet-700 ring-1 ring-violet-300'
              : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
          } disabled:opacity-50`}
        >
          <Brain className="w-3 h-3" />
          {t('modeDeep')}
        </button>
      </div>

      {/* Input row */}
      <div className="flex items-end gap-2 px-4 pb-4 pt-2">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={t('placeholder')}
          disabled={isLoading || disabled}
          rows={1}
          className="flex-1 resize-none rounded-xl border border-gray-200 px-4 py-2 text-sm focus:border-success focus:outline-none focus:ring-2 focus:ring-success/20 disabled:bg-gray-50 disabled:cursor-not-allowed"
        />
        <button
          onClick={handleSubmit}
          disabled={!input.trim() || isLoading || disabled}
          className={`flex-shrink-0 w-10 h-10 rounded-full text-white flex items-center justify-center transition-colors disabled:bg-gray-200 disabled:cursor-not-allowed ${
            mode === 'deep'
              ? 'bg-violet-600 hover:bg-violet-700'
              : 'bg-success hover:bg-success/90'
          }`}
        >
          {isLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </div>
    </div>
  );
}
