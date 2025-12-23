import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format date relative to now (e.g., "2 days ago", "today")
 */
export function formatRelativeDate(date: Date | string | null): string {
  if (!date) return '';

  const d = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'today';
  if (diffDays === 1) return '1 day ago';
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  return `${Math.floor(diffDays / 30)} months ago`;
}

/**
 * Format percentage with optional decimal places
 */
export function formatPercent(value: number, decimals: number = 0): string {
  return `${value.toFixed(decimals)}%`;
}

/**
 * Get mastery level badge class
 */
export function getMasteryBadgeClass(level: string | null): string {
  switch (level?.toUpperCase()) {
    case 'A':
      return 'mastery-badge mastery-badge-a';
    case 'B':
      return 'mastery-badge mastery-badge-b';
    case 'C':
      return 'mastery-badge mastery-badge-c';
    default:
      return 'mastery-badge mastery-badge-none';
  }
}

/**
 * Get mastery level color for charts
 */
export function getMasteryColor(level: string): string {
  switch (level?.toUpperCase()) {
    case 'A':
      return 'hsl(142, 76%, 36%)'; // Green
    case 'B':
      return 'hsl(38, 92%, 50%)';  // Amber
    case 'C':
      return 'hsl(0, 84%, 60%)';   // Red
    default:
      return 'hsl(215, 16%, 47%)'; // Gray
  }
}
