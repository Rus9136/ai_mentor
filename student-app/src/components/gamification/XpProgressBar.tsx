'use client';

interface XpProgressBarProps {
  currentXp: number;
  xpToNext: number;
  level: number;
  size?: 'sm' | 'md' | 'lg';
  showText?: boolean;
}

function getGradient(level: number): string {
  if (level < 5) return 'from-emerald-400 to-emerald-500';
  if (level < 10) return 'from-blue-400 to-blue-500';
  if (level < 15) return 'from-violet-400 to-violet-500';
  if (level < 20) return 'from-amber-400 to-amber-500';
  return 'from-rose-400 to-rose-500';
}

const heights = { sm: 'h-1.5', md: 'h-2.5', lg: 'h-3.5' };

export function XpProgressBar({
  currentXp,
  xpToNext,
  level,
  size = 'md',
  showText = true,
}: XpProgressBarProps) {
  const total = currentXp + xpToNext;
  const pct = total > 0 ? Math.min((currentXp / total) * 100, 100) : 0;

  return (
    <div className="w-full">
      <div className={`w-full overflow-hidden rounded-full bg-muted ${heights[size]}`}>
        <div
          className={`${heights[size]} rounded-full bg-gradient-to-r ${getGradient(level)} transition-all duration-700 ease-out`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {showText && (
        <p className="mt-1 text-xs text-muted-foreground">
          {currentXp.toLocaleString()} / {total.toLocaleString()} XP
        </p>
      )}
    </div>
  );
}
