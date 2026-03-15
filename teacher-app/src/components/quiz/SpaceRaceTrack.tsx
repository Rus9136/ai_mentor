'use client';

import { useTranslations } from 'next-intl';

interface TeamProgress {
  id: number;
  name: string;
  color: string;
  correct_answers: number;
  total_score: number;
}

interface SpaceRaceTrackProps {
  teams: TeamProgress[];
  totalQuestions: number;
}

export default function SpaceRaceTrack({ teams, totalQuestions }: SpaceRaceTrackProps) {
  const t = useTranslations('quiz');
  const finishLine = Math.max(1, totalQuestions);

  return (
    <div className="rounded-xl border bg-card p-6">
      <h3 className="mb-4 text-sm font-semibold text-muted-foreground">{t('spaceRace')}</h3>

      <div className="space-y-4">
        {teams.map((team) => {
          const progress = Math.min(100, (team.correct_answers / finishLine) * 100);
          return (
            <div key={team.id}>
              <div className="mb-1 flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded-full" style={{ backgroundColor: team.color }} />
                  <span className="font-medium">{team.name}</span>
                </div>
                <span className="text-muted-foreground">
                  {team.correct_answers}/{totalQuestions}
                </span>
              </div>
              <div className="relative h-8 w-full overflow-hidden rounded-full bg-muted">
                {/* Track line */}
                <div className="absolute right-2 top-0 h-full w-px bg-foreground/20" />
                {/* Rocket/progress */}
                <div
                  className="flex h-full items-center justify-end rounded-full px-2 transition-all duration-700 ease-out"
                  style={{
                    width: `${Math.max(8, progress)}%`,
                    backgroundColor: team.color,
                  }}
                >
                  <span className="text-sm">🚀</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Finish line label */}
      <div className="mt-2 flex justify-end">
        <span className="text-xs text-muted-foreground">🏁 {t('finishLine')}</span>
      </div>
    </div>
  );
}
