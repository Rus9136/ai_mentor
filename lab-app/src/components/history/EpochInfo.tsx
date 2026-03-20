'use client';

import { useTranslations } from 'next-intl';
import { X, BookOpen, Clock, Landmark, ScrollText } from 'lucide-react';
import type { EpochData } from '@/types/lab';

interface EpochInfoProps {
  epoch: EpochData;
  locale: string;
  onClose: () => void;
}

export function EpochInfo({ epoch, locale, onClose }: EpochInfoProps) {
  const t = useTranslations();
  const isKk = locale === 'kz';

  return (
    <div className="absolute top-0 right-0 bottom-0 z-[1001] w-80 max-w-[85vw] bg-card shadow-soft-lg border-l border-border flex flex-col animate-in slide-in-from-right">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex items-center gap-2">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: epoch.color }}
          />
          <h2 className="font-bold text-sm">{t('history.epoch')}</h2>
        </div>
        <button
          onClick={onClose}
          className="w-8 h-8 rounded-lg hover:bg-muted flex items-center justify-center"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <div>
          <h3 className="text-lg font-bold">
            {isKk ? epoch.name_kk : epoch.name}
          </h3>
          <div className="flex items-center gap-1.5 mt-1 text-sm text-muted-foreground">
            <Clock className="w-3.5 h-3.5" />
            {epoch.period}
          </div>
        </div>

        <p className="text-sm leading-relaxed">
          {isKk ? epoch.description_kk : epoch.description}
        </p>

        {/* Capital */}
        {epoch.capital && (
          <div className="card-flat p-3 space-y-1.5">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase">
              <Landmark className="w-3.5 h-3.5" />
              {t('history.capital')}
            </div>
            <p className="text-sm">{epoch.capital}</p>
          </div>
        )}

        {/* Key events */}
        {epoch.key_events.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase">
              <ScrollText className="w-3.5 h-3.5" />
              {t('history.events')}
            </div>
            <ul className="space-y-1.5">
              {epoch.key_events.map((event, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <span
                    className="w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0"
                    style={{ backgroundColor: epoch.color }}
                  />
                  {event}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Link to textbook paragraph */}
        {epoch.paragraph_id && (
          <a
            href={`https://ai-mentor.kz/ru/learn/${epoch.paragraph_id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-sm text-primary hover:underline"
          >
            <BookOpen className="w-4 h-4" />
            {t('history.readInTextbook')}
          </a>
        )}
      </div>
    </div>
  );
}
