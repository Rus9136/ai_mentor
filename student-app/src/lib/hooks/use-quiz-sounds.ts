'use client';

import { useRef, useState, useCallback, useEffect } from 'react';
import { QuizSoundManager } from '@/lib/quiz-sounds';

export type QuizSound =
  | 'lobby'
  | 'questionAppear'
  | 'tick'
  | 'timeUp'
  | 'correct'
  | 'incorrect'
  | 'streak'
  | 'result'
  | 'victory'
  | 'podiumCountdown'
  | 'podiumReveal'
  | 'powerupActivate';

export function useQuizSounds() {
  const mgr = useRef<QuizSoundManager | null>(null);
  const [muted, setMuted] = useState(false);

  useEffect(() => {
    const m = new QuizSoundManager();
    mgr.current = m;
    setMuted(m.muted);
    return () => m.dispose();
  }, []);

  const play = useCallback((sound: QuizSound) => {
    mgr.current?.[sound]();
  }, []);

  const toggleMute = useCallback(() => {
    if (mgr.current) {
      setMuted(mgr.current.toggleMute());
    }
  }, []);

  return { play, muted, toggleMute };
}
