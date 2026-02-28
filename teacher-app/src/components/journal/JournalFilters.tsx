'use client';

import { useTranslations } from 'next-intl';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { TeacherClassResponse } from '@/lib/api/teachers';
import type { SubjectListItem } from '@/types/grade';

interface JournalFiltersProps {
  classes: TeacherClassResponse[];
  subjects: SubjectListItem[];
  classId: number | null;
  subjectId: number | null;
  quarter: number;
  academicYear: string;
  onClassChange: (id: number | null) => void;
  onSubjectChange: (id: number | null) => void;
  onQuarterChange: (q: number) => void;
  onAcademicYearChange: (year: string) => void;
  locale: string;
}

const currentYear = new Date().getFullYear();
const yearOptions = [
  `${currentYear - 1}-${currentYear}`,
  `${currentYear}-${currentYear + 1}`,
];

export function JournalFilters({
  classes,
  subjects,
  classId,
  subjectId,
  quarter,
  academicYear,
  onClassChange,
  onSubjectChange,
  onQuarterChange,
  onAcademicYearChange,
  locale,
}: JournalFiltersProps) {
  const t = useTranslations('journal');

  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* Class */}
      <Select
        value={classId?.toString() ?? ''}
        onValueChange={(v) => onClassChange(v ? Number(v) : null)}
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder={t('selectClass')} />
        </SelectTrigger>
        <SelectContent>
          {classes.map((c) => (
            <SelectItem key={c.id} value={c.id.toString()}>
              {c.name} ({c.grade_level} {locale === 'kz' ? 'сынып' : 'класс'})
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Subject */}
      <Select
        value={subjectId?.toString() ?? ''}
        onValueChange={(v) => onSubjectChange(v ? Number(v) : null)}
      >
        <SelectTrigger className="w-[200px]">
          <SelectValue placeholder={t('selectSubject')} />
        </SelectTrigger>
        <SelectContent>
          {subjects.map((s) => (
            <SelectItem key={s.id} value={s.id.toString()}>
              {locale === 'kz' ? s.name_kz : s.name_ru}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Quarter */}
      <Select
        value={quarter.toString()}
        onValueChange={(v) => onQuarterChange(Number(v))}
      >
        <SelectTrigger className="w-[140px]">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {[1, 2, 3, 4].map((q) => (
            <SelectItem key={q} value={q.toString()}>
              {t('quarter')} {q}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Academic Year */}
      <Select value={academicYear} onValueChange={onAcademicYearChange}>
        <SelectTrigger className="w-[150px]">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {yearOptions.map((y) => (
            <SelectItem key={y} value={y}>
              {y}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
