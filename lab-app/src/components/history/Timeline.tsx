'use client';

import type { EpochData } from '@/types/lab';

interface TimelineProps {
  epochs: EpochData[];
  currentEpochId: string;
  onEpochChange: (id: string) => void;
}

export function Timeline({ epochs, currentEpochId, onEpochChange }: TimelineProps) {
  const currentIndex = epochs.findIndex((e) => e.id === currentEpochId);

  return (
    <div className="bg-card/95 backdrop-blur-sm border-t border-border px-4 py-3 pb-[env(safe-area-inset-bottom,0.75rem)]">
      {/* Epoch dots */}
      <div className="flex items-center justify-between mb-2 px-1">
        {epochs.map((epoch, index) => (
          <button
            key={epoch.id}
            onClick={() => onEpochChange(epoch.id)}
            className="flex flex-col items-center gap-1 group"
          >
            <div
              className={`w-4 h-4 rounded-full border-2 transition-all ${
                epoch.id === currentEpochId
                  ? 'scale-125 border-white shadow-lg'
                  : index < currentIndex
                    ? 'border-transparent opacity-70 hover:opacity-100'
                    : 'border-transparent opacity-40 hover:opacity-70'
              }`}
              style={{ backgroundColor: epoch.color }}
            />
          </button>
        ))}
      </div>

      {/* Slider */}
      <input
        type="range"
        min={0}
        max={epochs.length - 1}
        value={currentIndex}
        onChange={(e) => onEpochChange(epochs[parseInt(e.target.value)].id)}
        className="w-full h-1.5 rounded-full appearance-none cursor-pointer bg-muted
          [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5
          [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary [&::-webkit-slider-thumb]:shadow-md
          [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-white
          [&::-moz-range-thumb]:w-5 [&::-moz-range-thumb]:h-5 [&::-moz-range-thumb]:rounded-full
          [&::-moz-range-thumb]:bg-primary [&::-moz-range-thumb]:border-2 [&::-moz-range-thumb]:border-white"
      />

      {/* Current epoch label */}
      <div className="flex items-center justify-between mt-1 px-1">
        <span className="text-[10px] text-muted-foreground">{epochs[0].period.split('—')[0]}</span>
        <span className="text-xs font-semibold" style={{ color: epochs[currentIndex]?.color }}>
          {epochs[currentIndex]?.name}
        </span>
        <span className="text-[10px] text-muted-foreground">2026</span>
      </div>
    </div>
  );
}
