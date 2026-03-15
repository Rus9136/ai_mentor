'use client';

import { useEffect, useState, useRef } from 'react';
import { useTranslations } from 'next-intl';
import { Trophy, Star, Zap } from 'lucide-react';
import type { QuizFinishedData, LeaderboardEntry, TeamEntry } from '@/types/quiz';

interface QuizPodiumProps {
  data: QuizFinishedData;
  onPlaySound?: (sound: 'podiumCountdown' | 'podiumReveal') => void;
}

const MEDAL_EMOJI: Record<number, string> = { 1: '🥇', 2: '🥈', 3: '🥉' };

const PODIUM_COLORS = {
  1: 'from-yellow-400 to-amber-500',
  2: 'from-slate-300 to-slate-400',
  3: 'from-amber-600 to-amber-700',
};

const PODIUM_HEIGHTS = {
  1: 'h-44',
  2: 'h-32',
  3: 'h-24',
};

export default function QuizPodium({ data, onPlaySound }: QuizPodiumProps) {
  const t = useTranslations('quiz');
  const [countdown, setCountdown] = useState(3);
  const [showPodium, setShowPodium] = useState(false);
  const [showLeaderboard, setShowLeaderboard] = useState(false);
  const confettiFired = useRef(false);

  const top3 = data.leaderboard.slice(0, 3);
  // Display order: 2nd (left) | 1st (center) | 3rd (right)
  const podiumOrder = [top3[1], top3[0], top3[2]].filter(Boolean);

  useEffect(() => {
    if (countdown > 0) {
      onPlaySound?.('podiumCountdown');
      const timer = setTimeout(() => setCountdown((c) => c - 1), 1000);
      return () => clearTimeout(timer);
    }

    // Countdown finished — show podium
    setShowPodium(true);
    onPlaySound?.('podiumReveal');

    // Fire confetti after podium appears
    if (!confettiFired.current) {
      confettiFired.current = true;
      import('canvas-confetti').then((confetti) => {
        // Left burst
        confetti.default({ particleCount: 60, angle: 60, spread: 55, origin: { x: 0, y: 0.7 } });
        // Right burst
        confetti.default({ particleCount: 60, angle: 120, spread: 55, origin: { x: 1, y: 0.7 } });
        // Center burst after delay
        setTimeout(() => {
          confetti.default({ particleCount: 80, spread: 100, origin: { y: 0.5 } });
        }, 500);
      });
    }

    // Show leaderboard after podium animation settles
    const lbTimer = setTimeout(() => setShowLeaderboard(true), 2500);
    return () => clearTimeout(lbTimer);
  }, [countdown, onPlaySound]);

  // ── Countdown phase ──
  if (countdown > 0) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <div
          key={countdown}
          className="animate-bounce text-8xl font-black text-primary"
          style={{
            animation: 'countdownPulse 0.8s ease-out',
          }}
        >
          {countdown}
        </div>
        <style jsx>{`
          @keyframes countdownPulse {
            0% { transform: scale(2); opacity: 0; }
            50% { transform: scale(1.2); opacity: 1; }
            100% { transform: scale(1); opacity: 1; }
          }
        `}</style>
      </div>
    );
  }

  return (
    <div className="flex min-h-dvh flex-col items-center px-4 py-6">
      <h1 className="mb-6 text-2xl font-bold text-foreground">{t('finished')}</h1>

      {/* ── Podium ── */}
      <div className="mb-6 flex w-full max-w-sm items-end justify-center gap-2">
        {podiumOrder.map((entry, i) => {
          const place = i === 1 ? 1 : i === 0 ? 2 : 3;
          return (
            <div
              key={entry.rank}
              className="flex flex-1 flex-col items-center"
              style={{
                opacity: showPodium ? 1 : 0,
                transform: showPodium ? 'translateY(0)' : 'translateY(80px)',
                transition: `all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) ${place === 2 ? '0s' : place === 3 ? '0.4s' : '0.8s'}`,
              }}
            >
              {/* Medal + Name */}
              <div className="mb-2 text-center">
                <div className="text-3xl">{MEDAL_EMOJI[place]}</div>
                <p className="mt-1 text-xs font-semibold text-foreground truncate max-w-[90px]">
                  {entry.student_name}
                </p>
                <p className="text-xs text-muted-foreground">{entry.total_score}</p>
              </div>

              {/* Podium block */}
              <div
                className={`w-full rounded-t-xl bg-gradient-to-b ${PODIUM_COLORS[place as 1 | 2 | 3]} ${PODIUM_HEIGHTS[place as 1 | 2 | 3]} flex items-center justify-center ${
                  place === 1 ? 'shadow-lg shadow-yellow-400/30' : ''
                }`}
              >
                <span className="text-2xl font-black text-white/90">{place}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Your result ── */}
      <div
        className="mb-6 w-full max-w-sm rounded-2xl bg-card p-5 text-center shadow-lg"
        style={{
          opacity: showPodium ? 1 : 0,
          transition: 'opacity 0.5s ease 1.5s',
        }}
      >
        {data.your_rank && (
          <div className="mb-1 text-3xl">
            {MEDAL_EMOJI[data.your_rank] || `#${data.your_rank}`}
          </div>
        )}
        <p className="mb-1 text-lg font-semibold text-foreground">
          {t('yourRank', { rank: data.your_rank || '-' })}
        </p>
        <div className="flex items-center justify-center gap-4 text-sm text-muted-foreground">
          <span className="flex items-center gap-1">
            <Star className="h-4 w-4 text-primary" />
            {data.your_score} {t('score')}
          </span>
          <span className="flex items-center gap-1">
            <Zap className="h-4 w-4 text-amber-500" />
            +{data.xp_earned} XP
          </span>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          {t('correctAnswers', { correct: data.correct_answers, total: data.total_questions })}
        </p>
      </div>

      {/* ── Team leaderboard ── */}
      {data.team_leaderboard && data.team_leaderboard.length > 0 && (
        <div
          className="mb-6 w-full max-w-sm"
          style={{ opacity: showLeaderboard ? 1 : 0, transition: 'opacity 0.5s ease' }}
        >
          <h3 className="mb-3 text-sm font-semibold text-muted-foreground">{t('teamStandings')}</h3>
          <div className="space-y-2">
            {data.team_leaderboard.map((team, i) => (
              <div key={team.id} className="flex items-center justify-between rounded-xl px-4 py-3 bg-card">
                <div className="flex items-center gap-3">
                  <span className="text-lg font-bold text-muted-foreground">#{i + 1}</span>
                  <span className="h-4 w-4 rounded-full" style={{ backgroundColor: team.color }} />
                  <span className="font-medium text-foreground">{team.name}</span>
                </div>
                <span className="font-bold text-foreground">{team.total_score}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Full leaderboard ── */}
      <div
        className="w-full max-w-sm"
        style={{ opacity: showLeaderboard ? 1 : 0, transition: 'opacity 0.5s ease' }}
      >
        <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-muted-foreground">
          <Trophy className="h-4 w-4" />
          {t('leaderboard')}
        </h3>
        <div className="space-y-2">
          {data.leaderboard.map((entry) => (
            <div
              key={entry.rank}
              className={`flex items-center justify-between rounded-xl px-4 py-3 ${
                entry.rank === data.your_rank ? 'bg-primary/10 ring-2 ring-primary' : 'bg-card'
              }`}
            >
              <div className="flex items-center gap-3">
                <span className="w-6 text-center text-sm font-bold text-muted-foreground">
                  {MEDAL_EMOJI[entry.rank] || `${entry.rank}`}
                </span>
                <span className="text-sm font-medium text-foreground">{entry.student_name}</span>
              </div>
              <div className="text-right">
                <span className="text-sm font-bold text-foreground">{entry.total_score}</span>
                {entry.xp_earned ? (
                  <span className="ml-2 text-xs text-amber-500">+{entry.xp_earned} XP</span>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
