'use client';

import { useState } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import {
  Loader2,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  Users,
  BarChart3,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useHomeworkSubmissions } from '@/lib/hooks/use-homework';
import type {
  StudentSubmissionDetail,
  StudentAnswerDetail,
  StudentHomeworkStatus,
} from '@/types/homework';

interface StudentResultsTabProps {
  homeworkId: number;
}

export function StudentResultsTab({ homeworkId }: StudentResultsTabProps) {
  const t = useTranslations('homework.results');
  const locale = useLocale();
  const { data, isLoading, error } = useHomeworkSubmissions(homeworkId);
  const [expandedStudentId, setExpandedStudentId] = useState<number | null>(null);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-destructive">{t('noStudents')}</p>
      </div>
    );
  }

  if (data.students.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">{t('noStudents')}</p>
      </div>
    );
  }

  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString(locale === 'kz' ? 'kk-KZ' : 'ru-RU', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const toggleStudent = (studentId: number) => {
    setExpandedStudentId(expandedStudentId === studentId ? null : studentId);
  };

  return (
    <div className="space-y-4">
      {/* Summary stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">{t('studentName')}</span>
            </div>
            <p className="text-2xl font-bold mt-1">{data.total_students}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">{t('status')}</span>
            </div>
            <p className="text-2xl font-bold mt-1">
              {data.submitted_count}/{data.total_students}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">{t('averageScore')}</span>
            </div>
            <p className="text-2xl font-bold mt-1">
              {data.average_percentage != null ? `${data.average_percentage}%` : '—'}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">{t('needsReview')}</span>
            </div>
            <p className="text-2xl font-bold mt-1">
              {data.students.filter(s => s.answers.some(a => a.flagged_for_review)).length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Students table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-8"></TableHead>
                <TableHead>{t('studentName')}</TableHead>
                <TableHead>{t('status')}</TableHead>
                <TableHead>{t('score')}</TableHead>
                <TableHead>{t('submittedAt')}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.students.map((student) => (
                <>
                  <TableRow
                    key={student.student_id}
                    className="cursor-pointer"
                    onClick={() => toggleStudent(student.student_id)}
                  >
                    <TableCell>
                      {student.answers.length > 0 ? (
                        expandedStudentId === student.student_id ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )
                      ) : null}
                    </TableCell>
                    <TableCell className="font-medium">
                      {student.student_name}
                      {student.late_submitted && (
                        <Badge variant="warning" className="ml-2 text-[10px]">
                          <Clock className="h-3 w-3 mr-1" />
                          {t('submissionStatus.submitted')}
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <SubmissionStatusBadge status={student.status as StudentHomeworkStatus} t={t} />
                    </TableCell>
                    <TableCell>
                      {student.percentage != null ? (
                        <span className={
                          student.percentage >= 70
                            ? 'text-green-600 font-semibold'
                            : student.percentage >= 40
                              ? 'text-amber-600 font-semibold'
                              : 'text-red-600 font-semibold'
                        }>
                          {Math.round(student.percentage)}%
                        </span>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {student.submitted_at ? (
                        <span className="text-sm">{formatDate(student.submitted_at)}</span>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                  </TableRow>
                  {expandedStudentId === student.student_id && student.answers.length > 0 && (
                    <TableRow key={`${student.student_id}-answers`}>
                      <TableCell colSpan={5} className="bg-muted/30 p-4">
                        <StudentAnswersList answers={student.answers} t={t} />
                      </TableCell>
                    </TableRow>
                  )}
                </>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

function SubmissionStatusBadge({
  status,
  t,
}: {
  status: StudentHomeworkStatus;
  t: ReturnType<typeof useTranslations>;
}) {
  const variantMap: Record<string, 'secondary' | 'info' | 'warning' | 'success' | 'default'> = {
    assigned: 'secondary',
    in_progress: 'info',
    submitted: 'warning',
    graded: 'success',
    returned: 'default',
  };

  return (
    <Badge variant={variantMap[status] || 'secondary'}>
      {t(`submissionStatus.${status}`)}
    </Badge>
  );
}

function StudentAnswersList({
  answers,
  t,
}: {
  answers: StudentAnswerDetail[];
  t: ReturnType<typeof useTranslations>;
}) {
  return (
    <div className="space-y-3">
      {answers.map((answer, index) => (
        <div
          key={answer.id}
          className="bg-background rounded-lg border p-3 space-y-2"
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <p className="text-sm font-medium text-muted-foreground">
                {t('question')} {index + 1}
              </p>
              <p className="text-sm mt-0.5">{answer.question_text}</p>
            </div>
            <div className="flex items-center gap-2 ml-4">
              <AnswerScoreBadge answer={answer} t={t} />
              {answer.flagged_for_review && (
                <Badge variant="warning">
                  <AlertTriangle className="h-3 w-3 mr-1" />
                  {t('needsReview')}
                </Badge>
              )}
            </div>
          </div>

          {/* Student answer */}
          <div className="text-sm">
            <span className="text-muted-foreground">{t('studentAnswer')}: </span>
            {answer.answer_text || answer.answer_code ? (
              <span>{answer.answer_text || answer.answer_code}</span>
            ) : answer.selected_option_ids && answer.options ? (
              <span>
                {answer.selected_option_ids
                  .map(id => {
                    const opt = answer.options?.find(o => o.id === id);
                    return opt ? `${id}) ${opt.text}` : id;
                  })
                  .join(', ')}
              </span>
            ) : (
              <span className="italic text-muted-foreground">{t('noAnswer')}</span>
            )}
          </div>

          {/* Correct answer for comparison */}
          {answer.correct_answer && (
            <div className="text-sm">
              <span className="text-muted-foreground">{t('correctAnswer')}: </span>
              <span>{answer.correct_answer}</span>
            </div>
          )}

          {/* AI feedback */}
          {answer.ai_feedback && (
            <div className="text-sm bg-blue-50 dark:bg-blue-950/30 rounded p-2">
              <span className="text-muted-foreground font-medium">{t('aiFeedback')}: </span>
              <span>{answer.ai_feedback}</span>
            </div>
          )}

          {/* Teacher comment */}
          {answer.teacher_comment && (
            <div className="text-sm bg-green-50 dark:bg-green-950/30 rounded p-2">
              <span className="text-muted-foreground font-medium">{t('teacherFeedback')}: </span>
              <span>{answer.teacher_comment}</span>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function AnswerScoreBadge({
  answer,
  t,
}: {
  answer: StudentAnswerDetail;
  t: ReturnType<typeof useTranslations>;
}) {
  // Teacher override takes precedence
  if (answer.teacher_override_score != null) {
    return (
      <Badge variant="success">
        {Math.round(answer.teacher_override_score * 100)}%
      </Badge>
    );
  }

  // Auto-graded (closed questions)
  if (answer.is_correct != null) {
    return answer.is_correct ? (
      <Badge variant="success">
        <CheckCircle2 className="h-3 w-3 mr-1" />
        {t('correct')}
      </Badge>
    ) : (
      <Badge variant="destructive">
        <XCircle className="h-3 w-3 mr-1" />
        {t('incorrect')}
      </Badge>
    );
  }

  // AI graded
  if (answer.ai_score != null) {
    return (
      <Badge variant="info">
        {Math.round(answer.ai_score * 100)}%
      </Badge>
    );
  }

  return null;
}
