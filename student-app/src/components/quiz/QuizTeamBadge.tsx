'use client';

interface QuizTeamBadgeProps {
  teamName: string;
  teamColor: string;
}

export default function QuizTeamBadge({ teamName, teamColor }: QuizTeamBadgeProps) {
  return (
    <div
      className="inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-sm font-semibold text-white"
      style={{ backgroundColor: teamColor }}
    >
      <span className="h-2 w-2 rounded-full bg-white/50" />
      {teamName}
    </div>
  );
}
