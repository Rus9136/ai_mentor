'use client';

import { useState, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { useLocale } from 'next-intl';
import { BookOpen, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { JournalFilters, JournalGrid, GradeDialog } from '@/components/journal';
import { useClasses, useClassDetail } from '@/lib/hooks/use-teacher-data';
import { useClassGrades, useSubjects, useCreateGrade, useUpdateGrade, useDeleteGrade } from '@/lib/hooks/use-grades';
import type { GradeResponse, GradeCreate, GradeUpdate } from '@/types/grade';

function getCurrentAcademicYear(): string {
  const now = new Date();
  const year = now.getFullYear();
  // If before September, academic year started last year
  if (now.getMonth() < 8) return `${year - 1}-${year}`;
  return `${year}-${year + 1}`;
}

function getCurrentQuarter(): number {
  const month = new Date().getMonth(); // 0-based
  if (month >= 8 && month <= 9) return 1;   // Sep-Oct
  if (month >= 10 || month === 0) return 2;  // Nov-Jan
  if (month >= 1 && month <= 2) return 3;    // Feb-Mar
  return 4;                                   // Apr-May
}

export default function JournalPage() {
  const t = useTranslations('journal');
  const locale = useLocale();

  // Filters state
  const [classId, setClassId] = useState<number | null>(null);
  const [subjectId, setSubjectId] = useState<number | null>(null);
  const [quarter, setQuarter] = useState(getCurrentQuarter());
  const [academicYear, setAcademicYear] = useState(getCurrentAcademicYear());

  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedGrade, setSelectedGrade] = useState<GradeResponse | null>(null);
  const [prefilledStudentId, setPrefilledStudentId] = useState<number | null>(null);
  const [prefilledDate, setPrefilledDate] = useState<string | null>(null);

  // Data queries
  const { data: classes = [] } = useClasses();
  const { data: subjects = [] } = useSubjects();
  const { data: classDetail } = useClassDetail(classId ?? 0);
  const { data: grades = [], isLoading: gradesLoading } = useClassGrades(
    classId ?? 0,
    subjectId ?? 0,
    { quarter, academic_year: academicYear }
  );

  // Mutations
  const createGrade = useCreateGrade();
  const updateGrade = useUpdateGrade();
  const deleteGrade = useDeleteGrade();
  const isSaving = createGrade.isPending || updateGrade.isPending || deleteGrade.isPending;

  // Students from class detail
  const students = (classDetail?.students ?? []).map((s) => ({
    id: s.id,
    first_name: s.first_name,
    last_name: s.last_name,
  }));

  // Handlers
  const handleCellClick = useCallback((studentId: number, date: string) => {
    setSelectedGrade(null);
    setPrefilledStudentId(studentId);
    setPrefilledDate(date);
    setDialogOpen(true);
  }, []);

  const handleGradeClick = useCallback((grade: GradeResponse) => {
    setSelectedGrade(grade);
    setPrefilledStudentId(null);
    setPrefilledDate(null);
    setDialogOpen(true);
  }, []);

  const handleAddClick = useCallback(() => {
    setSelectedGrade(null);
    setPrefilledStudentId(null);
    setPrefilledDate(null);
    setDialogOpen(true);
  }, []);

  const handleSave = useCallback(
    (data: { student_id: number; grade_value: number; grade_type: string; grade_date: string; comment?: string }) => {
      if (!subjectId || !classId) return;
      const payload: GradeCreate = {
        student_id: data.student_id,
        subject_id: subjectId,
        class_id: classId,
        grade_value: data.grade_value,
        grade_type: data.grade_type as GradeCreate['grade_type'],
        grade_date: data.grade_date,
        quarter,
        academic_year: academicYear,
        comment: data.comment,
      };
      createGrade.mutate(payload, { onSuccess: () => setDialogOpen(false) });
    },
    [subjectId, classId, quarter, academicYear, createGrade]
  );

  const handleUpdate = useCallback(
    (gradeId: number, data: GradeUpdate) => {
      updateGrade.mutate({ gradeId, data }, { onSuccess: () => setDialogOpen(false) });
    },
    [updateGrade]
  );

  const handleDelete = useCallback(
    (gradeId: number) => {
      deleteGrade.mutate(gradeId, { onSuccess: () => setDialogOpen(false) });
    },
    [deleteGrade]
  );

  const showGrid = classId && subjectId;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <BookOpen className="h-5 w-5 text-primary" />
          </div>
          <h1 className="text-2xl font-bold">{t('title')}</h1>
        </div>
        {showGrid && (
          <Button onClick={handleAddClick} size="sm">
            <Plus className="mr-1 h-4 w-4" />
            {t('addGrade')}
          </Button>
        )}
      </div>

      {/* Filters */}
      <JournalFilters
        classes={classes}
        subjects={subjects}
        classId={classId}
        subjectId={subjectId}
        quarter={quarter}
        academicYear={academicYear}
        onClassChange={setClassId}
        onSubjectChange={setSubjectId}
        onQuarterChange={setQuarter}
        onAcademicYearChange={setAcademicYear}
        locale={locale}
      />

      {/* Grid or placeholder */}
      {showGrid ? (
        gradesLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          </div>
        ) : (
          <JournalGrid
            grades={grades}
            students={students}
            onCellClick={handleCellClick}
            onGradeClick={handleGradeClick}
          />
        )
      ) : (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-16 text-muted-foreground">
          <BookOpen className="mb-3 h-10 w-10" />
          <p>{t('noData')}</p>
        </div>
      )}

      {/* Grade Dialog */}
      {showGrid && (
        <GradeDialog
          open={dialogOpen}
          onClose={() => setDialogOpen(false)}
          grade={selectedGrade}
          prefilledStudentId={prefilledStudentId}
          prefilledDate={prefilledDate}
          students={students}
          subjectId={subjectId}
          classId={classId}
          quarter={quarter}
          academicYear={academicYear}
          onSave={handleSave}
          onUpdate={handleUpdate}
          onDelete={handleDelete}
          isSaving={isSaving}
        />
      )}
    </div>
  );
}
