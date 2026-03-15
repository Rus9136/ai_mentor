'use client';

import { useTranslations } from 'next-intl';
import { useQuizMatrix } from '@/lib/hooks/use-quiz';
import { Loader2 } from 'lucide-react';

interface QuizLiveMatrixProps {
  sessionId: number;
}

interface MatrixAnswer {
  question_index: number;
  is_correct: boolean;
  answer_time_ms: number;
  text_answer?: string;
}

interface MatrixStudent {
  student_id: number;
  student_name: string;
  answers: (MatrixAnswer | null)[];
}

interface MatrixData {
  students: MatrixStudent[];
  question_count: number;
}

export default function QuizLiveMatrix({ sessionId }: QuizLiveMatrixProps) {
  const t = useTranslations('quiz');
  const { data, isLoading } = useQuizMatrix(sessionId);

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const matrix = data as MatrixData | undefined;
  if (!matrix || matrix.students.length === 0) {
    return <p className="py-8 text-center text-sm text-muted-foreground">{t('noParticipants')}</p>;
  }

  const questionNumbers = Array.from({ length: matrix.question_count }, (_, i) => i + 1);

  return (
    <div className="rounded-xl border bg-card p-4">
      <h3 className="mb-4 text-sm font-semibold">{t('matrixView')}</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr>
              <th className="sticky left-0 z-10 bg-card px-3 py-2 text-left font-medium">{t('rank')}</th>
              {questionNumbers.map((n) => (
                <th key={n} className="px-2 py-2 text-center font-medium">Q{n}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matrix.students.map((student) => (
              <tr key={student.student_id} className="border-t">
                <td className="sticky left-0 z-10 bg-card px-3 py-2 font-medium whitespace-nowrap">
                  {student.student_name}
                </td>
                {student.answers.map((ans, qi) => (
                  <td key={qi} className="px-2 py-2 text-center">
                    {ans === null ? (
                      <span className="inline-block h-6 w-6 rounded-full bg-muted" title="Нет ответа" />
                    ) : ans.is_correct ? (
                      <span
                        className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-green-100 text-green-700"
                        title={`${(ans.answer_time_ms / 1000).toFixed(1)}s`}
                      >
                        ✓
                      </span>
                    ) : (
                      <span
                        className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-red-100 text-red-600"
                        title={`${(ans.answer_time_ms / 1000).toFixed(1)}s`}
                      >
                        ✗
                      </span>
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
