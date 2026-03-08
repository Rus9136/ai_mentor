'use client';

import { useTranslations } from 'next-intl';

export type ViewMode = 'split' | 'reading' | 'chat';

interface ViewToggleProps {
  mode: ViewMode;
  onChange: (mode: ViewMode) => void;
}

export function ViewToggle({ mode, onChange }: ViewToggleProps) {
  const t = useTranslations('paragraph');

  const tabs: { value: ViewMode; label: string }[] = [
    { value: 'split', label: t('viewMode.split') },
    { value: 'reading', label: t('viewMode.reading') },
    { value: 'chat', label: t('viewMode.chat') },
  ];

  return (
    <div className="hidden md:flex gap-0.5 bg-[#EDE8E3] rounded-[10px] p-[3px]">
      {tabs.map((tab) => (
        <button
          key={tab.value}
          onClick={() => onChange(tab.value)}
          className={`px-3.5 py-[5px] rounded-[8px] text-xs font-bold transition-all ${
            mode === tab.value
              ? 'bg-white text-foreground shadow-sm'
              : 'text-[#A09080] hover:text-foreground'
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
