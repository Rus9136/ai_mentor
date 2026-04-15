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
  parchment: {
    name: 'parchment',
    label: 'Пергамент',
    bg: {
      title:   '',
      content: '',
      terms:   '',
      summary: '',
    },
    bgColor: {
      title:   '#FAF3E8',
      content: '#FAF3E8',
      terms:   '#FAF3E8',
      summary: '#6D2E46',
    },
    titleColor: 'text-[#2C1810]',
    subtitleColor: 'text-[#7A6558]',
    headingColor: 'text-[#2C1810]',
    bodyColor: 'text-[#2C1810]',
    accentColor: 'text-[#6D2E46]',
    accentBg: 'bg-[#6D2E46]/10',
    accentBorder: 'border-[#6D2E46]',
    badgeBg: 'bg-[#6D2E46]',
    badgeText: 'text-white',
    cardBg: 'bg-white/85',
    cardText: 'text-[#2C1810]',
    cardBorder: 'border-[#D4A574]/50',
    correctBg: 'bg-emerald-100/80',
    correctBorder: 'border-emerald-600',
    correctText: 'text-emerald-800',
    optionBg: 'bg-white/80',
    checkBg: 'bg-[#6D2E46]',
    statBg: 'bg-[#6D2E46]',
    statText: 'text-white',
    statLabel: 'text-[#D4A574]',
  },
  slate: {
    name: 'slate',
    label: 'Минимализм',
    bg: {
      title:   '',
      content: '',
      terms:   '',
      summary: '',
    },
    bgColor: {
      title:   '#F5F5F7',
      content: '#F5F5F7',
      terms:   '#F5F5F7',
      summary: '#36454F',
    },
    titleColor: 'text-[#1D1D1F]',
    subtitleColor: 'text-[#86868B]',
    headingColor: 'text-[#1D1D1F]',
    bodyColor: 'text-[#1D1D1F]',
    accentColor: 'text-[#6B8F71]',
    accentBg: 'bg-[#6B8F71]/10',
    accentBorder: 'border-[#6B8F71]',
    badgeBg: 'bg-[#36454F]',
    badgeText: 'text-white',
    cardBg: 'bg-white/90',
    cardText: 'text-[#1D1D1F]',
    cardBorder: 'border-gray-200/60',
    correctBg: 'bg-emerald-100/80',
    correctBorder: 'border-emerald-600',
    correctText: 'text-emerald-800',
    optionBg: 'bg-white/85',
    checkBg: 'bg-[#6B8F71]',
    statBg: 'bg-[#36454F]',
    statText: 'text-white',
    statLabel: 'text-gray-300',
  },
  electric: {
    name: 'electric',
    label: 'Электрик',
    bg: {
      title:   '',
      content: '',
      terms:   '',
      summary: '',
    },
    bgColor: {
      title:   '#F8FAFC',
      content: '#F8FAFC',
      terms:   '#F8FAFC',
      summary: '#2563EB',
    },
    titleColor: 'text-[#0F172A]',
    subtitleColor: 'text-[#64748B]',
    headingColor: 'text-[#0F172A]',
    bodyColor: 'text-[#0F172A]',
    accentColor: 'text-[#2563EB]',
    accentBg: 'bg-[#2563EB]/10',
    accentBorder: 'border-[#2563EB]',
    badgeBg: 'bg-[#2563EB]',
    badgeText: 'text-white',
    cardBg: 'bg-white/90',
    cardText: 'text-[#0F172A]',
    cardBorder: 'border-blue-200/60',
    correctBg: 'bg-emerald-100/80',
    correctBorder: 'border-emerald-600',
    correctText: 'text-emerald-800',
    optionBg: 'bg-white/85',
    checkBg: 'bg-[#F59E0B]',
    statBg: 'bg-[#2563EB]',
    statText: 'text-white',
    statLabel: 'text-blue-200',
  },
  lavender: {
    name: 'lavender',
    label: 'Лаванда',
    bg: {
      title:   '',
      content: '',
      terms:   '',
      summary: '',
    },
    bgColor: {
      title:   '#F5F0FF',
      content: '#F5F0FF',
      terms:   '#F5F0FF',
      summary: '#7C3AED',
    },
    titleColor: 'text-[#1E1B4B]',
    subtitleColor: 'text-[#6B7280]',
    headingColor: 'text-[#1E1B4B]',
    bodyColor: 'text-[#1E1B4B]',
    accentColor: 'text-[#7C3AED]',
    accentBg: 'bg-[#7C3AED]/10',
    accentBorder: 'border-[#7C3AED]',
    badgeBg: 'bg-[#7C3AED]',
    badgeText: 'text-white',
    cardBg: 'bg-white/90',
    cardText: 'text-[#1E1B4B]',
    cardBorder: 'border-purple-200/60',
    correctBg: 'bg-emerald-100/80',
    correctBorder: 'border-emerald-600',
    correctText: 'text-emerald-800',
    optionBg: 'bg-white/85',
    checkBg: 'bg-[#F472B6]',
    statBg: 'bg-[#7C3AED]',
    statText: 'text-white',
    statLabel: 'text-purple-200',
  },
  coral: {
    name: 'coral',
    label: 'Коралл',
    bg: {
      title:   '',
      content: '',
      terms:   '',
      summary: '',
    },
    bgColor: {
      title:   '#FFF5F2',
      content: '#FFF5F2',
      terms:   '#FFF5F2',
      summary: '#E8553D',
    },
    titleColor: 'text-[#27150E]',
    subtitleColor: 'text-[#9A7B70]',
    headingColor: 'text-[#27150E]',
    bodyColor: 'text-[#27150E]',
    accentColor: 'text-[#E8553D]',
    accentBg: 'bg-[#E8553D]/10',
    accentBorder: 'border-[#E8553D]',
    badgeBg: 'bg-[#E8553D]',
    badgeText: 'text-white',
    cardBg: 'bg-white/90',
    cardText: 'text-[#27150E]',
    cardBorder: 'border-orange-200/60',
    correctBg: 'bg-emerald-100/80',
    correctBorder: 'border-emerald-600',
    correctText: 'text-emerald-800',
    optionBg: 'bg-white/85',
    checkBg: 'bg-[#FBBF24]',
    statBg: 'bg-[#E8553D]',
    statText: 'text-white',
    statLabel: 'text-orange-100',
  },
  ocean: {
    name: 'ocean',
    label: 'Океан',
    bg: {
      title:   '',
      content: '',
      terms:   '',
      summary: '',
    },
    bgColor: {
      title:   '#EFF6FF',
      content: '#EFF6FF',
      terms:   '#EFF6FF',
      summary: '#065A82',
    },
    titleColor: 'text-[#0C2340]',
    subtitleColor: 'text-[#5B7A99]',
    headingColor: 'text-[#0C2340]',
    bodyColor: 'text-[#0C2340]',
    accentColor: 'text-[#065A82]',
    accentBg: 'bg-[#065A82]/10',
    accentBorder: 'border-[#065A82]',
    badgeBg: 'bg-[#065A82]',
    badgeText: 'text-white',
    cardBg: 'bg-white/90',
    cardText: 'text-[#0C2340]',
    cardBorder: 'border-sky-200/60',
    correctBg: 'bg-emerald-100/80',
    correctBorder: 'border-emerald-600',
    correctText: 'text-emerald-800',
    optionBg: 'bg-white/85',
    checkBg: 'bg-[#0EA5E9]',
    statBg: 'bg-[#065A82]',
    statText: 'text-white',
    statLabel: 'text-sky-200',
  },
  sage: {
    name: 'sage',
    label: 'Шалфей',
    bg: {
      title:   '',
      content: '',
      terms:   '',
      summary: '',
    },
    bgColor: {
      title:   '#F2F7F2',
      content: '#F2F7F2',
      terms:   '#F2F7F2',
      summary: '#5F7161',
    },
    titleColor: 'text-[#1A2E1A]',
    subtitleColor: 'text-[#6B7C6B]',
    headingColor: 'text-[#1A2E1A]',
    bodyColor: 'text-[#1A2E1A]',
    accentColor: 'text-[#5F7161]',
    accentBg: 'bg-[#5F7161]/10',
    accentBorder: 'border-[#5F7161]',
    badgeBg: 'bg-[#5F7161]',
    badgeText: 'text-white',
    cardBg: 'bg-white/90',
    cardText: 'text-[#1A2E1A]',
    cardBorder: 'border-green-200/60',
    correctBg: 'bg-emerald-100/80',
    correctBorder: 'border-emerald-600',
    correctText: 'text-emerald-800',
    optionBg: 'bg-white/85',
    checkBg: 'bg-[#D4A574]',
    statBg: 'bg-[#5F7161]',
    statText: 'text-white',
    statLabel: 'text-green-200',
  },
};

/** Subject code → default theme mapping (mirrors backend SUBJECT_THEME_MAP) */
export const SUBJECT_THEME_DEFAULTS: Record<string, SlideThemeName> = {
  history_kz: 'warm',
  world_history: 'parchment',
  biology: 'forest',
  natural_science: 'sage',
  chemistry: 'electric',
  geography: 'ocean',
  algebra: 'midnight',
  geometry: 'midnight',
  math: 'midnight',
  informatics: 'electric',
  physics: 'midnight',
  kazakh_language: 'lavender',
  russian_language: 'lavender',
  english_language: 'slate',
  literature: 'parchment',
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
