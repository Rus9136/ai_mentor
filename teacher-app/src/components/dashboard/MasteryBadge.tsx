import { cn } from '@/lib/utils';

interface MasteryBadgeProps {
  level: string | null;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export function MasteryBadge({
  level,
  size = 'md',
  showLabel = false,
}: MasteryBadgeProps) {
  const getStyles = () => {
    switch (level?.toUpperCase()) {
      case 'A':
        return 'mastery-badge-a';
      case 'B':
        return 'mastery-badge-b';
      case 'C':
        return 'mastery-badge-c';
      default:
        return 'mastery-badge-none';
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case 'sm':
        return 'h-6 w-6 text-xs';
      case 'lg':
        return 'h-10 w-10 text-lg';
      default:
        return 'h-8 w-8 text-sm';
    }
  };

  const getLabel = () => {
    switch (level?.toUpperCase()) {
      case 'A':
        return 'A';
      case 'B':
        return 'B';
      case 'C':
        return 'C';
      default:
        return '-';
    }
  };

  if (showLabel && level) {
    return (
      <span className={cn('mastery-badge', getStyles())}>
        {getLabel()}
      </span>
    );
  }

  return (
    <div
      className={cn(
        'inline-flex items-center justify-center rounded-full font-bold',
        getStyles(),
        getSizeStyles()
      )}
    >
      {getLabel()}
    </div>
  );
}
