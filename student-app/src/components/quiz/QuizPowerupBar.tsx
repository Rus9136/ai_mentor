'use client';

import { useTranslations } from 'next-intl';

interface PowerupDef {
  type: string;
  icon: string;
  cost: number;
  labelKey: string;
}

const POWERUPS: PowerupDef[] = [
  { type: 'double_points', icon: '✕2', cost: 50, labelKey: 'doublePoints' },
  { type: 'fifty_fifty', icon: '½', cost: 75, labelKey: 'fiftyFifty' },
  { type: 'time_freeze', icon: '❄', cost: 40, labelKey: 'timeFreeze' },
  { type: 'shield', icon: '🛡', cost: 60, labelKey: 'shield' },
];

interface QuizPowerupBarProps {
  studentXp: number;
  activePowerup: string | null;
  onActivate: (type: string) => void;
  enabled: boolean;
}

export default function QuizPowerupBar({
  studentXp,
  activePowerup,
  onActivate,
  enabled,
}: QuizPowerupBarProps) {
  const t = useTranslations('quiz');

  if (!enabled) return null;

  return (
    <div className="mb-3 flex items-center justify-center gap-2">
      {POWERUPS.map((p) => {
        const isActive = activePowerup === p.type;
        const canAfford = studentXp >= p.cost;
        const isDisabled = !!activePowerup || !canAfford;

        return (
          <button
            key={p.type}
            onClick={() => !isDisabled && onActivate(p.type)}
            disabled={isDisabled}
            className={`flex flex-col items-center rounded-xl px-3 py-2 text-xs font-medium transition-all ${
              isActive
                ? 'bg-green-500/20 ring-2 ring-green-500 text-green-700'
                : isDisabled
                  ? 'bg-muted/50 text-muted-foreground opacity-50'
                  : 'bg-card hover:bg-primary/10 text-foreground hover:scale-105 active:scale-95'
            }`}
          >
            <span className="text-lg leading-none">{p.icon}</span>
            <span className="mt-0.5 text-[10px]">{t(`powerups.${p.labelKey}`)}</span>
            <span className={`text-[10px] ${canAfford ? 'text-amber-500' : 'text-red-400'}`}>
              {p.cost} XP
            </span>
          </button>
        );
      })}
    </div>
  );
}
