'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { GradeType } from '@/types/grade';
import type { GradeResponse } from '@/types/grade';

interface Student {
  id: number;
  first_name: string;
  last_name: string;
}

interface GradeDialogProps {
  open: boolean;
  onClose: () => void;
  // Edit mode: existing grade
  grade?: GradeResponse | null;
  // Create mode: pre-filled data
  prefilledStudentId?: number | null;
  prefilledDate?: string | null;
  // Context
  students: Student[];
  subjectId: number;
  classId: number;
  quarter: number;
  academicYear: string;
  // Actions
  onSave: (data: {
    student_id: number;
    grade_value: number;
    grade_type: GradeType;
    grade_date: string;
    comment?: string;
  }) => void;
  onUpdate: (
    gradeId: number,
    data: {
      grade_value?: number;
      grade_type?: GradeType;
      grade_date?: string;
      comment?: string;
    }
  ) => void;
  onDelete: (gradeId: number) => void;
  isSaving: boolean;
}

export function GradeDialog({
  open,
  onClose,
  grade,
  prefilledStudentId,
  prefilledDate,
  students,
  subjectId,
  classId,
  quarter,
  academicYear,
  onSave,
  onUpdate,
  onDelete,
  isSaving,
}: GradeDialogProps) {
  const t = useTranslations('journal');
  const isEdit = !!grade;

  const [studentId, setStudentId] = useState<number | null>(null);
  const [gradeValue, setGradeValue] = useState('');
  const [gradeType, setGradeType] = useState<GradeType>(GradeType.CURRENT);
  const [gradeDate, setGradeDate] = useState('');
  const [comment, setComment] = useState('');
  const [confirmDelete, setConfirmDelete] = useState(false);

  useEffect(() => {
    if (!open) {
      setConfirmDelete(false);
      return;
    }
    if (grade) {
      setStudentId(grade.student_id);
      setGradeValue(grade.grade_value.toString());
      setGradeType(grade.grade_type);
      setGradeDate(grade.grade_date);
      setComment(grade.comment ?? '');
    } else {
      setStudentId(prefilledStudentId ?? null);
      setGradeValue('');
      setGradeType(GradeType.CURRENT);
      setGradeDate(prefilledDate ?? new Date().toISOString().slice(0, 10));
      setComment('');
    }
  }, [open, grade, prefilledStudentId, prefilledDate]);

  const handleSubmit = () => {
    const value = parseInt(gradeValue, 10);
    if (!studentId || isNaN(value) || value < 1 || value > 10 || !gradeDate) return;

    if (isEdit && grade) {
      onUpdate(grade.id, {
        grade_value: value,
        grade_type: gradeType,
        grade_date: gradeDate,
        comment: comment || undefined,
      });
    } else {
      onSave({
        student_id: studentId,
        grade_value: value,
        grade_type: gradeType,
        grade_date: gradeDate,
        comment: comment || undefined,
      });
    }
  };

  const sortedStudents = [...students].sort((a, b) =>
    a.last_name.localeCompare(b.last_name)
  );

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{isEdit ? t('editGrade') : t('addGrade')}</DialogTitle>
          <DialogDescription className="sr-only">
            {isEdit ? t('editGrade') : t('addGrade')}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Student */}
          <div className="space-y-2">
            <Label>{t('student')}</Label>
            <Select
              value={studentId?.toString() ?? ''}
              onValueChange={(v) => setStudentId(Number(v))}
              disabled={isEdit || !!prefilledStudentId}
            >
              <SelectTrigger>
                <SelectValue placeholder={t('selectClass')} />
              </SelectTrigger>
              <SelectContent>
                {sortedStudents.map((s) => (
                  <SelectItem key={s.id} value={s.id.toString()}>
                    {s.last_name} {s.first_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Grade value */}
          <div className="space-y-2">
            <Label>{t('grade')} (1-10)</Label>
            <Input
              type="number"
              min={1}
              max={10}
              value={gradeValue}
              onChange={(e) => setGradeValue(e.target.value)}
              placeholder="1-10"
            />
          </div>

          {/* Grade type */}
          <div className="space-y-2">
            <Label>{t('gradeType')}</Label>
            <Select
              value={gradeType}
              onValueChange={(v) => setGradeType(v as GradeType)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.values(GradeType).map((type) => (
                  <SelectItem key={type} value={type}>
                    {t(`types.${type}`)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Date */}
          <div className="space-y-2">
            <Label>{t('date')}</Label>
            <Input
              type="date"
              value={gradeDate}
              onChange={(e) => setGradeDate(e.target.value)}
            />
          </div>

          {/* Comment */}
          <div className="space-y-2">
            <Label>{t('comment')}</Label>
            <Textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={2}
              placeholder={t('comment')}
            />
          </div>
        </div>

        <DialogFooter className="gap-2">
          {isEdit && grade && (
            <>
              {confirmDelete ? (
                <div className="mr-auto flex items-center gap-2">
                  <span className="text-sm text-destructive">{t('confirmDelete')}</span>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => onDelete(grade.id)}
                    disabled={isSaving}
                  >
                    {t('deleteGrade')}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setConfirmDelete(false)}
                  >
                    {t('cancel')}
                  </Button>
                </div>
              ) : (
                <Button
                  variant="outline"
                  className="mr-auto text-destructive hover:text-destructive"
                  onClick={() => setConfirmDelete(true)}
                >
                  {t('deleteGrade')}
                </Button>
              )}
            </>
          )}
          <Button variant="outline" onClick={onClose} disabled={isSaving}>
            {t('cancel')}
          </Button>
          <Button onClick={handleSubmit} disabled={isSaving}>
            {isSaving ? '...' : isEdit ? t('editGrade') : t('addGrade')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
