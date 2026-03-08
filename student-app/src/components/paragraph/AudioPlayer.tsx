'use client';

import { useState } from 'react';
import { Headphones, Volume2, Pause, Play, RotateCcw } from 'lucide-react';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type TranslateFunction = (key: string, values?: Record<string, any>) => string;

interface AudioPlayerProps {
  audioUrl: string | null | undefined;
  t: TranslateFunction;
}

export function AudioPlayer({ audioUrl, t }: AudioPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  const formatTime = (time: number) => {
    const mins = Math.floor(time / 60);
    const secs = Math.floor(time % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (!audioUrl) {
    return (
      <div className="card-elevated p-8 text-center">
        <Headphones className="mx-auto h-12 w-12 text-muted-foreground/50" />
        <p className="mt-4 text-muted-foreground">{t('noAudio')}</p>
      </div>
    );
  }

  return (
    <div className="card-elevated p-6">
      <div className="flex flex-col items-center">
        <div className="w-32 h-32 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mb-6">
          <Volume2 className="h-12 w-12 text-primary" />
        </div>

        <audio
          src={audioUrl}
          onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
          onLoadedMetadata={(e) => setDuration(e.currentTarget.duration)}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          onEnded={() => setIsPlaying(false)}
          id="audio-player"
          className="hidden"
        />

        <div className="w-full max-w-md mb-4">
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-primary transition-all"
              style={{ width: `${duration ? (currentTime / duration) * 100 : 0}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-muted-foreground mt-1">
            <span>{formatTime(currentTime)}</span>
            <span>{formatTime(duration)}</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button
            onClick={() => {
              const audio = document.getElementById('audio-player') as HTMLAudioElement;
              if (audio) audio.currentTime = 0;
            }}
            className="p-3 rounded-full bg-muted hover:bg-muted/80 transition-all"
          >
            <RotateCcw className="h-5 w-5 text-muted-foreground" />
          </button>

          <button
            onClick={() => {
              const audio = document.getElementById('audio-player') as HTMLAudioElement;
              if (audio) {
                if (isPlaying) audio.pause();
                else audio.play();
              }
            }}
            className="p-4 rounded-full bg-primary text-primary-foreground hover:opacity-90 transition-all"
          >
            {isPlaying ? <Pause className="h-6 w-6" /> : <Play className="h-6 w-6 ml-0.5" />}
          </button>

          <div className="w-12" />
        </div>
      </div>
    </div>
  );
}
