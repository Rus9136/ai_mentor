import type { SubjectBrief } from '../../lib/api/textbooks';

// Subject icons by code (preferred, from normalized subjects table)
export const SUBJECT_ICONS_BY_CODE: Record<string, string> = {
  'history_kz': '📜',
  'world_history': '📜',
  'math': '📐',
  'algebra': '📐',
  'geometry': '📐',
  'physics': '⚡',
  'biology': '🧬',
  'chemistry': '🧪',
  'geography': '🌍',
  'informatics': '💻',
  'english_lang': '🇬🇧',
  'kazakh_lang': '🇰🇿',
  'russian_lang': '📝',
  'kazakh_lit': '📚',
  'russian_lit': '📚',
  'world_lit': '📚',
  'art': '🎨',
  'music': '🎵',
  'pe': '⚽',
  'tech': '🔧',
  'law': '⚖️',
};

// Subject colors by code
export const SUBJECT_COLORS_BY_CODE: Record<string, string> = {
  'history_kz': 'bg-amber-500',
  'world_history': 'bg-amber-600',
  'math': 'bg-blue-500',
  'algebra': 'bg-blue-500',
  'geometry': 'bg-blue-600',
  'physics': 'bg-purple-500',
  'biology': 'bg-green-500',
  'chemistry': 'bg-red-500',
  'geography': 'bg-teal-500',
  'informatics': 'bg-indigo-500',
  'english_lang': 'bg-pink-500',
  'kazakh_lang': 'bg-cyan-500',
  'russian_lang': 'bg-orange-500',
  'kazakh_lit': 'bg-rose-500',
  'russian_lit': 'bg-rose-600',
  'world_lit': 'bg-rose-400',
  'art': 'bg-fuchsia-500',
  'music': 'bg-violet-500',
  'pe': 'bg-lime-500',
  'tech': 'bg-slate-500',
  'law': 'bg-stone-500',
};

// Legacy: Subject icons by text (for backward compatibility)
export const SUBJECT_ICONS: Record<string, string> = {
  'история': '📜',
  'история казахстана': '📜',
  'всемирная история': '📜',
  'алгебра': '📐',
  'математика': '📐',
  'геометрия': '📐',
  'физика': '⚡',
  'биология': '🧬',
  'химия': '🧪',
  'география': '🌍',
  'информатика': '💻',
  'английский': '🇬🇧',
  'казахский': '🇰🇿',
  'русский': '📝',
  'литература': '📚',
};

// Legacy: Subject colors by text (for backward compatibility)
export const SUBJECT_COLORS: Record<string, string> = {
  'история': 'bg-amber-500',
  'история казахстана': 'bg-amber-500',
  'всемирная история': 'bg-amber-600',
  'алгебра': 'bg-blue-500',
  'математика': 'bg-blue-500',
  'геометрия': 'bg-blue-600',
  'физика': 'bg-purple-500',
  'биология': 'bg-green-500',
  'химия': 'bg-red-500',
  'география': 'bg-teal-500',
  'информатика': 'bg-indigo-500',
  'английский': 'bg-pink-500',
  'казахский': 'bg-cyan-500',
  'русский': 'bg-orange-500',
  'литература': 'bg-rose-500',
};

/**
 * Get icon for a subject. Prefers code-based lookup if SubjectBrief is provided.
 */
export function getSubjectIcon(subject: string, subjectRel?: SubjectBrief | null): string {
  // Prefer code-based lookup
  if (subjectRel?.code && SUBJECT_ICONS_BY_CODE[subjectRel.code]) {
    return SUBJECT_ICONS_BY_CODE[subjectRel.code];
  }
  // Fallback to text-based lookup
  const key = subject.toLowerCase();
  for (const [keyword, icon] of Object.entries(SUBJECT_ICONS)) {
    if (key.includes(keyword)) return icon;
  }
  return '📚';
}

/**
 * Get color class for a subject. Prefers code-based lookup if SubjectBrief is provided.
 */
export function getSubjectColor(subject: string, subjectRel?: SubjectBrief | null): string {
  // Prefer code-based lookup
  if (subjectRel?.code && SUBJECT_COLORS_BY_CODE[subjectRel.code]) {
    return SUBJECT_COLORS_BY_CODE[subjectRel.code];
  }
  // Fallback to text-based lookup
  const key = subject.toLowerCase();
  for (const [keyword, color] of Object.entries(SUBJECT_COLORS)) {
    if (key.includes(keyword)) return color;
  }
  return 'bg-gray-500';
}
