'use client';

import { useTranslations } from 'next-intl';
import { Users, Loader2 } from 'lucide-react';

interface QuizLobbyProps {
  participantCount: number;
  teamName?: string | null;
  teamColor?: string | null;
}

export default function QuizLobby({ participantCount, teamName, teamColor }: QuizLobbyProps) {
  const t = useTranslations('quiz');

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center px-4 text-center">
      <Loader2 className="mb-6 h-12 w-12 animate-spin text-primary" />
      <h2 className="mb-4 text-xl font-bold text-foreground">{t('waitingForStart')}</h2>

      {teamName && teamColor && (
        <div
          className="mb-4 inline-flex items-center gap-2 rounded-full px-5 py-2 text-sm font-semibold text-white"
          style={{ backgroundColor: teamColor }}
        >
          <span className="h-2.5 w-2.5 rounded-full bg-white/50" />
          {teamName}
        </div>
      )}

      <div className="flex items-center gap-2 text-muted-foreground">
        <Users className="h-5 w-5" />
        <span className="text-lg">{t('connected', { count: participantCount })}</span>
      </div>
    </div>
  );
}
