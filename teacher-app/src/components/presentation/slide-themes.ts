import type { SlideThemeName } from '@/types/presentation';

export interface SlideThemeConfig {
  name: SlideThemeName;
  label: string;
  /** Background: image URL or empty string (use bgColor fallback) */
  bg: {
    title: string;
    content: string;
    terms: string;
    summary: string;
  };
  /** Fallback CSS background colors when bg images are empty */
  bgColor: {
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
  /** Primary color for stat_callout card background */
  statBg: string;
  statText: string;
  statLabel: string;
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
    bgColor: {
      title:   '#FFF8F2',
      content: '#FFF8F2',
      terms:   '#FFF8F2',
      summary: '#E88134',
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
    statBg: 'bg-amber-600',
    statText: 'text-white',
    statLabel: 'text-amber-100',
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
    bgColor: {
      title:   '#F4F8F1',
      content: '#F4F8F1',
      terms:   '#F4F8F1',
      summary: '#2C5F2D',
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
    statBg: 'bg-emerald-700',
    statText: 'text-white',
    statLabel: 'text-emerald-100',
  },
  forest: {
    name: 'forest',
    label: 'Естественные науки (изумрудный)',
    bg: {
      title:   '/slide-bg/biology/title.png',
      content: '/slide-bg/biology/content.png',
      terms:   '/slide-bg/biology/terms.png',
      summary: '/slide-bg/biology/summary.png',
    },
    bgColor: {
      title:   '#F4F8F1',
      content: '#F4F8F1',
      terms:   '#F4F8F1',
      summary: '#2C5F2D',
    },
    titleColor: 'text-slate-800',
    subtitleColor: 'text-slate-600',
    headingColor: 'text-slate-800',
    bodyColor: 'text-slate-700',
    accentColor: 'text-emerald-700',
    accentBg: 'bg-emerald-50/80',
    accentBorder: 'border-emerald-600',
    badgeBg: 'bg-emerald-700',
    badgeText: 'text-white',
    cardBg: 'bg-white/85',
    cardText: 'text-slate-800',
    cardBorder: 'border-emerald-200/60',
    correctBg: 'bg-emerald-100/90',
    correctBorder: 'border-emerald-500',
    correctText: 'text-emerald-800',
    optionBg: 'bg-white/85',
    checkBg: 'bg-emerald-600',
    statBg: 'bg-emerald-700',
    statText: 'text-white',
    statLabel: 'text-emerald-100',
  },
  midnight: {
    name: 'midnight',
    label: 'Информатика (тёмный)',
    bg: {
      title:   '',
      content: '',
      terms:   '',
      summary: '',
    },
    bgColor: {
      title:   '#101428',
      content: '#101428',
      terms:   '#101428',
      summary: '#6E8BFF',
    },
    titleColor: 'text-slate-100',
    subtitleColor: 'text-slate-300',
    headingColor: 'text-slate-100',
    bodyColor: 'text-slate-200',
    accentColor: 'text-indigo-400',
    accentBg: 'bg-indigo-950/60',
    accentBorder: 'border-indigo-500',
    badgeBg: 'bg-indigo-600',
    badgeText: 'text-white',
    cardBg: 'bg-slate-800/80',
    cardText: 'text-slate-100',
    cardBorder: 'border-slate-600/50',
    correctBg: 'bg-emerald-900/60',
    correctBorder: 'border-emerald-500',
    correctText: 'text-emerald-300',
    optionBg: 'bg-slate-800/80',
    checkBg: 'bg-amber-500',
    statBg: 'bg-indigo-600',
    statText: 'text-white',
    statLabel: 'text-indigo-200',
  },
};

export function getTheme(name?: string): SlideThemeConfig {
  return THEMES[(name as SlideThemeName) || 'warm'] || THEMES.warm;
}

/** Get background style — image if available, else solid color */
export function getSlideBg(theme: SlideThemeConfig, slideType: keyof SlideThemeConfig['bg']): React.CSSProperties {
  const bgImage = theme.bg[slideType];
  const bgColor = theme.bgColor[slideType];
  if (bgImage) {
    return { backgroundImage: `url(${bgImage})`, backgroundColor: bgColor };
  }
  return { backgroundColor: bgColor };
}
