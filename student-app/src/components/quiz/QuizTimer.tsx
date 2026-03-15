'use client';

import { useEffect, useRef, useState } from 'react';

interface QuizTimerProps {
  totalMs: number;
  onExpire: () => void;
  onUrgentTick?: () => void;
}

export default function QuizTimer({ totalMs, onExpire, onUrgentTick }: QuizTimerProps) {
  const [remaining, setRemaining] = useState(totalMs);
  const startTimeRef = useRef(Date.now());
  const animRef = useRef<number>(0);
  const expiredRef = useRef(false);
  const lastTickedSec = useRef(-1);
  const urgentTickRef = useRef(onUrgentTick);
  urgentTickRef.current = onUrgentTick;

  useEffect(() => {
    startTimeRef.current = Date.now();
    expiredRef.current = false;
    lastTickedSec.current = -1;
    setRemaining(totalMs);

    const tick = () => {
      const elapsed = Date.now() - startTimeRef.current;
      const left = Math.max(0, totalMs - elapsed);
      setRemaining(left);

      // Urgent tick sound (once per second when <= 5s)
      const sec = Math.ceil(left / 1000);
      if (sec <= 5 && sec > 0 && sec !== lastTickedSec.current) {
        lastTickedSec.current = sec;
        urgentTickRef.current?.();
      }

      if (left <= 0 && !expiredRef.current) {
        expiredRef.current = true;
        onExpire();
        return;
      }
      animRef.current = requestAnimationFrame(tick);
    };

    animRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animRef.current);
  }, [totalMs, onExpire]);

  const seconds = Math.ceil(remaining / 1000);
  const progress = remaining / totalMs;
  const isUrgent = seconds <= 5;

  // SVG circle
  const size = 64;
  const strokeWidth = 4;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - progress);

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-muted-foreground/20"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className={`transition-colors ${isUrgent ? 'text-red-500' : 'text-primary'}`}
        />
      </svg>
      <span className={`absolute text-lg font-bold ${isUrgent ? 'text-red-500' : 'text-foreground'}`}>
        {seconds}
      </span>
    </div>
  );
}
