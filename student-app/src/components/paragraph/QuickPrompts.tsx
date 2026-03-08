'use client';

import { useTranslations } from 'next-intl';
import { Sparkles, Info, CheckSquare, AlertTriangle, FileText } from 'lucide-react';

interface QuickPromptsProps {
  onSendPrompt: (text: string) => void;
}

export function QuickPrompts({ onSendPrompt }: QuickPromptsProps) {
  const t = useTranslations('paragraph');

  const prompts = [
    { key: 'explain', icon: Info, text: t('quickPrompts.explain') },
    { key: 'questions', icon: CheckSquare, text: t('quickPrompts.questions') },
    { key: 'ent', icon: AlertTriangle, text: t('quickPrompts.ent') },
    { key: 'cheatsheet', icon: FileText, text: t('quickPrompts.cheatsheet') },
  ];

  return (
    <div className="bg-gradient-to-br from-success/10 to-primary/5 border border-success/30 rounded-[14px] p-4 my-5">
      <div className="flex items-center gap-2 mb-3">
        <div className="flex h-6 w-6 items-center justify-center rounded-[7px] bg-success">
          <Sparkles className="h-3.5 w-3.5 text-white" />
        </div>
        <span className="text-[13px] font-extrabold text-foreground">
          {t('quickPrompts.title')}
        </span>
      </div>
      <div className="flex flex-wrap gap-2">
        {prompts.map((prompt) => (
          <button
            key={prompt.key}
            onClick={() => onSendPrompt(prompt.text)}
            className="flex items-center gap-1.5 bg-white border-[1.5px] border-[#EDE8E3] text-[#4A3D33] px-3.5 py-2 rounded-[10px] text-xs font-bold hover:border-primary hover:text-primary hover:bg-primary/5 transition-all"
          >
            <prompt.icon className="h-3.5 w-3.5" />
            {prompt.text}
          </button>
        ))}
      </div>
    </div>
  );
}
