import type { SlideThemeName } from '@/types/presentation';

export interface SlideThemeConfig {
  name: SlideThemeName;
  label: string;
  // Title slide
  titleGradient: string;
  titleText: string;
  titleSubtext: string;
  titleDecor: string;
  // Content slides
  slideBg: string;
  headingColor: string;
  bodyColor: string;
  accentColor: string;
  accentBg: string;
  accentBorder: string;
  // Badges
  badgeBg: string;
  badgeText: string;
  // Header bar
  headerBg: string;
  headerText: string;
  headerAccent: string;
  // Quiz
  correctBg: string;
  correctBorder: string;
  correctText: string;
  optionBg: string;
  optionBorder: string;
  // Summary
  checkColor: string;
  summaryHeaderBg: string;
  // Cards
  cardBg: string;
  cardBorder: string;
  cardShadow: string;
}

export const THEMES: Record<SlideThemeName, SlideThemeConfig> = {
  blue: {
    name: 'blue',
    label: 'Академический (синий)',
    titleGradient: 'bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-900',
    titleText: 'text-white',
    titleSubtext: 'text-blue-200',
    titleDecor: 'bg-blue-400/20',
    slideBg: 'bg-gradient-to-br from-slate-50 to-blue-50/30',
    headingColor: 'text-slate-800',
    bodyColor: 'text-slate-600',
    accentColor: 'text-blue-600',
    accentBg: 'bg-blue-50',
    accentBorder: 'border-blue-400',
    badgeBg: 'bg-blue-600',
    badgeText: 'text-white',
    headerBg: 'bg-gradient-to-r from-blue-700 to-indigo-800',
    headerText: 'text-white',
    headerAccent: 'bg-blue-400',
    correctBg: 'bg-emerald-50',
    correctBorder: 'border-emerald-400',
    correctText: 'text-emerald-700',
    optionBg: 'bg-white',
    optionBorder: 'border-slate-200',
    checkColor: 'text-emerald-500',
    summaryHeaderBg: 'bg-gradient-to-r from-blue-800 to-indigo-900',
    cardBg: 'bg-white',
    cardBorder: 'border-slate-200/60',
    cardShadow: 'shadow-sm',
  },
  green: {
    name: 'green',
    label: 'Биология (зелёный)',
    titleGradient: 'bg-gradient-to-br from-emerald-600 via-teal-700 to-cyan-900',
    titleText: 'text-white',
    titleSubtext: 'text-emerald-200',
    titleDecor: 'bg-emerald-400/20',
    slideBg: 'bg-gradient-to-br from-slate-50 to-emerald-50/30',
    headingColor: 'text-slate-800',
    bodyColor: 'text-slate-600',
    accentColor: 'text-emerald-600',
    accentBg: 'bg-emerald-50',
    accentBorder: 'border-emerald-400',
    badgeBg: 'bg-emerald-600',
    badgeText: 'text-white',
    headerBg: 'bg-gradient-to-r from-emerald-700 to-teal-800',
    headerText: 'text-white',
    headerAccent: 'bg-emerald-400',
    correctBg: 'bg-emerald-50',
    correctBorder: 'border-emerald-400',
    correctText: 'text-emerald-700',
    optionBg: 'bg-white',
    optionBorder: 'border-slate-200',
    checkColor: 'text-emerald-500',
    summaryHeaderBg: 'bg-gradient-to-r from-teal-800 to-cyan-900',
    cardBg: 'bg-white',
    cardBorder: 'border-slate-200/60',
    cardShadow: 'shadow-sm',
  },
  warm: {
    name: 'warm',
    label: 'История (тёплый)',
    titleGradient: 'bg-gradient-to-br from-amber-600 via-orange-700 to-red-900',
    titleText: 'text-white',
    titleSubtext: 'text-amber-200',
    titleDecor: 'bg-amber-400/20',
    slideBg: 'bg-gradient-to-br from-slate-50 to-amber-50/30',
    headingColor: 'text-slate-800',
    bodyColor: 'text-slate-600',
    accentColor: 'text-amber-700',
    accentBg: 'bg-amber-50',
    accentBorder: 'border-amber-400',
    badgeBg: 'bg-amber-600',
    badgeText: 'text-white',
    headerBg: 'bg-gradient-to-r from-amber-700 to-orange-800',
    headerText: 'text-white',
    headerAccent: 'bg-amber-400',
    correctBg: 'bg-emerald-50',
    correctBorder: 'border-emerald-400',
    correctText: 'text-emerald-700',
    optionBg: 'bg-white',
    optionBorder: 'border-slate-200',
    checkColor: 'text-emerald-500',
    summaryHeaderBg: 'bg-gradient-to-r from-amber-800 to-red-900',
    cardBg: 'bg-white',
    cardBorder: 'border-slate-200/60',
    cardShadow: 'shadow-sm',
  },
};

export function getTheme(name?: string): SlideThemeConfig {
  return THEMES[(name as SlideThemeName) || 'blue'] || THEMES.blue;
}
