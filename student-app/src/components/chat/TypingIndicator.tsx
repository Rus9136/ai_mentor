'use client';

interface TypingIndicatorProps {
  text?: string;
}

export function TypingIndicator({ text }: TypingIndicatorProps) {
  return (
    <div className="flex items-center gap-3 py-3">
      <div className="flex gap-1">
        <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
        <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
        <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
      </div>
      {text && <span className="text-sm text-gray-500">{text}</span>}
    </div>
  );
}
