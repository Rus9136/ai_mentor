import type { SlideThemeName } from '@/types/presentation';

export interface SlideThemeConfig {
  name: SlideThemeName;
  label: string;
  bg: {
    title: string;
    content: string;
    terms: string;
    summary: string;
  };
  titleColor: string;
  subtitleColor: string;
  headingColor: string;
  bodyColor: string;
  accentColor: string;
  accentBg: string;
  accentBorder: string;
  badgeBg: string;
  badgeText: string;
  cardBg: string;
  cardText: string;
  cardBorder: string;
  correctBg: string;
  correctBorder: string;
  correctText: string;
  optionBg: string;
  checkBg: string;
}

export const THEMES: Record<SlideThemeName, SlideThemeConfig> = {
  warm: {
    name: 'warm',
    label: 'История (тёплый)',
    bg: {
      title:   '/slide-bg/history/title.png',
      content: '/slide-bg/history/content.png',
      terms:   '/slide-bg/history/terms.png',
      summary: '/slide-bg/history/summary.png',
    },
    titleColor: 'text-amber-950',
    subtitleColor: 'text-amber-800',
    headingColor: 'text-amber-950',
    bodyColor: 'text-amber-900',
    accentColor: 'text-amber-700',
    accentBg: 'bg-amber-800/10',
    accentBorder: 'border-amber-700',
    badgeBg: 'bg-amber-800',
    badgeText: 'text-amber-50',
    cardBg: 'bg-amber-50/80',
    cardText: 'text-amber-950',
    cardBorder: 'border-amber-300/50',
    correctBg: 'bg-emerald-100/80',
    correctBorder: 'border-emerald-600',
    correctText: 'text-emerald-800',
    optionBg: 'bg-amber-50/80',
    checkBg: 'bg-emerald-700',
  },
  green: {
    name: 'green',
    label: 'Биология (зелёный)',
    bg: {
      title:   '/slide-bg/biology/title.png',
      content: '/slide-bg/biology/content.png',
      terms:   '/slide-bg/biology/terms.png',
      summary: '/slide-bg/biology/summary.png',
    },
    titleColor: 'text-slate-800',
    subtitleColor: 'text-slate-600',
    headingColor: 'text-slate-800',
    bodyColor: 'text-slate-700',
    accentColor: 'text-orange-600',
    accentBg: 'bg-orange-50/80',
    accentBorder: 'border-orange-400',
    badgeBg: 'bg-orange-500',
    badgeText: 'text-white',
    cardBg: 'bg-white/85',
    cardText: 'text-slate-800',
    cardBorder: 'border-orange-200/60',
    correctBg: 'bg-emerald-100/90',
    correctBorder: 'border-emerald-500',
    correctText: 'text-emerald-800',
    optionBg: 'bg-white/85',
    checkBg: 'bg-emerald-600',
  },
};

export function getTheme(name?: string): SlideThemeConfig {
  return THEMES[(name as SlideThemeName) || 'warm'] || THEMES.warm;
}
