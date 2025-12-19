// Subject icons mapping
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

// Subject colors mapping
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

export function getSubjectIcon(subject: string): string {
  const key = subject.toLowerCase();
  for (const [keyword, icon] of Object.entries(SUBJECT_ICONS)) {
    if (key.includes(keyword)) return icon;
  }
  return '📚';
}

export function getSubjectColor(subject: string): string {
  const key = subject.toLowerCase();
  for (const [keyword, color] of Object.entries(SUBJECT_COLORS)) {
    if (key.includes(keyword)) return color;
  }
  return 'bg-gray-500';
}
