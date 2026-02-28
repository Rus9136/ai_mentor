'use client';

import { useMemo } from 'react';
import { useTranslations } from 'next-intl';
import { cn } from '@/lib/utils';
import type { GradeResponse } from '@/types/grade';
import { GradeType } from '@/types/grade';

interface Student {
  id: number;
  first_name: string;
  last_name: string;
}

interface DateColumn {
  date: string;
  type: GradeType | null;
}

interface JournalGridProps {
  grades: GradeResponse[];
  students: Student[];
  onCellClick: (studentId: number, date: string) => void;
  onGradeClick: (grade: GradeResponse) => void;
}

function gradeColor(value: number): string {
  if (value >= 8) return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400';
  if (value >= 5) return 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400';
  return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
}

function formatDate(dateStr: string): string {
  const [, m, d] = dateStr.split('-');
  return `${d}.${m}`;
}

function gradeTypeLabel(type: GradeType | null): string | null {
  if (!type || type === GradeType.CURRENT) return null;
  return type;
}

export function JournalGrid({ grades, students, onCellClick, onGradeClick }: JournalGridProps) {
  const t = useTranslations('journal');

  const { dateColumns, gradeMap, averages } = useMemo(() => {
    // 1. Unique sorted dates
    const dateSet = new Set(grades.map((g) => g.grade_date));
    const sortedDates = [...dateSet].sort();

    // 2. Date column info (date + grade type label)
    const cols: DateColumn[] = sortedDates.map((d) => {
      const g = grades.find((gr) => gr.grade_date === d);
      return { date: d, type: g?.grade_type ?? null };
    });

    // 3. Build gradeMap: student_id -> date -> Grade
    const map = new Map<number, Map<string, GradeResponse>>();
    for (const g of grades) {
      if (!map.has(g.student_id)) map.set(g.student_id, new Map());
      map.get(g.student_id)!.set(g.grade_date, g);
    }

    // 4. Averages per student
    const avgs = new Map<number, number>();
    for (const s of students) {
      const studentGrades = grades.filter((g) => g.student_id === s.id);
      if (studentGrades.length > 0) {
        const sum = studentGrades.reduce((acc, g) => acc + g.grade_value, 0);
        avgs.set(s.id, sum / studentGrades.length);
      }
    }

    return { dateColumns: cols, gradeMap: map, averages: avgs };
  }, [grades, students]);

  const sortedStudents = useMemo(
    () => [...students].sort((a, b) => a.last_name.localeCompare(b.last_name)),
    [students]
  );

  if (students.length === 0) {
    return (
      <div className="flex items-center justify-center py-12 text-muted-foreground">
        {t('noData')}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="bg-muted/50">
            <th className="sticky left-0 z-10 min-w-[180px] border-b border-r bg-muted/50 px-3 py-2 text-left font-medium">
              {t('student')}
            </th>
            {dateColumns.map((col) => (
              <th
                key={col.date}
                className="min-w-[60px] border-b px-2 py-2 text-center font-medium"
              >
                <div>{formatDate(col.date)}</div>
                {gradeTypeLabel(col.type) && (
                  <div className="text-[10px] font-normal text-muted-foreground">
                    {gradeTypeLabel(col.type)}
                  </div>
                )}
              </th>
            ))}
            <th className="min-w-[70px] border-b border-l px-2 py-2 text-center font-medium">
              {t('average')}
            </th>
          </tr>
        </thead>
        <tbody>
          {sortedStudents.map((student) => {
            const avg = averages.get(student.id);
            return (
              <tr key={student.id} className="hover:bg-muted/30">
                <td className="sticky left-0 z-10 border-b border-r bg-background px-3 py-2 font-medium">
                  {student.last_name} {student.first_name}
                </td>
                {dateColumns.map((col) => {
                  const grade = gradeMap.get(student.id)?.get(col.date);
                  return (
                    <td
                      key={col.date}
                      className="border-b px-2 py-2 text-center"
                    >
                      {grade ? (
                        <button
                          onClick={() => onGradeClick(grade)}
                          className={cn(
                            'inline-flex h-7 w-7 items-center justify-center rounded font-semibold transition-opacity hover:opacity-80',
                            gradeColor(grade.grade_value)
                          )}
                        >
                          {grade.grade_value}
                        </button>
                      ) : (
                        <button
                          onClick={() => onCellClick(student.id, col.date)}
                          className="inline-flex h-7 w-7 items-center justify-center rounded text-muted-foreground/30 transition-colors hover:bg-muted hover:text-muted-foreground"
                        >
                          +
                        </button>
                      )}
                    </td>
                  );
                })}
                <td className="border-b border-l px-2 py-2 text-center font-semibold">
                  {avg !== undefined ? avg.toFixed(1) : '—'}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
