'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { ArrowLeft, Plus, FileQuestion } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { RoleGuard } from '@/components/auth';
import { QuestionCard } from '@/components/tests/question-card';
import { QuestionDialog } from '@/components/tests/question-dialog';
import {
  useTest,
  useQuestions,
  useCreateQuestion,
  useUpdateQuestion,
  useDeleteQuestion,
} from '@/lib/hooks/use-tests';
import type { Question } from '@/types';
import type { QuestionCreateInput } from '@/lib/validations/test';

export default function QuestionsPage() {
  const params = useParams();
  const router = useRouter();
  const t = useTranslations('tests');
  const locale = 'ru';

  const testId = Number(params.id);
  const { data: test, isLoading: testLoading } = useTest(testId, false);
  const { data: questions = [], isLoading: questionsLoading } = useQuestions(
    testId,
    false
  );

  const createQuestion = useCreateQuestion(false);
  const updateQuestion = useUpdateQuestion(false);
  const deleteQuestion = useDeleteQuestion(false);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState<Question | undefined>();

  const handleCreateClick = () => {
    setEditingQuestion(undefined);
    setDialogOpen(true);
  };

  const handleEditClick = (question: Question) => {
    setEditingQuestion(question);
    setDialogOpen(true);
  };

  const handleDelete = (question: Question) => {
    deleteQuestion.mutate({ id: question.id, testId });
  };

  const handleSubmit = (data: QuestionCreateInput) => {
    if (editingQuestion) {
      updateQuestion.mutate(
        {
          id: editingQuestion.id,
          testId,
          data,
        },
        {
          onSuccess: () => {
            setDialogOpen(false);
            setEditingQuestion(undefined);
          },
        }
      );
    } else {
      createQuestion.mutate(
        { testId, data },
        {
          onSuccess: () => {
            setDialogOpen(false);
          },
        }
      );
    }
  };

  const isLoading = testLoading || questionsLoading;
  const sortedQuestions = [...questions].sort(
    (a, b) => a.sort_order - b.sort_order
  );

  if (isLoading) {
    return (
      <RoleGuard allowedRoles={['super_admin']}>
        <div className="space-y-6">
          <Skeleton className="h-8 w-64" />
          <div className="grid gap-4">
            <Skeleton className="h-40 w-full" />
            <Skeleton className="h-40 w-full" />
          </div>
        </div>
      </RoleGuard>
    );
  }

  if (!test) {
    return (
      <RoleGuard allowedRoles={['super_admin']}>
        <div className="text-center py-12">
          <p className="text-muted-foreground">Тест не найден</p>
          <Button variant="link" onClick={() => router.push(`/${locale}/tests`)}>
            Вернуться к списку
          </Button>
        </div>
      </RoleGuard>
    );
  }

  return (
    <RoleGuard allowedRoles={['super_admin']}>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.push(`/${locale}/tests/${testId}`)}
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">
                {t('questions')}
              </h1>
              <p className="text-muted-foreground">
                {test.title} • {questions.length} вопросов
              </p>
            </div>
          </div>
          <Button onClick={handleCreateClick}>
            <Plus className="mr-2 h-4 w-4" />
            {t('addQuestion')}
          </Button>
        </div>

        {questions.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted mb-4">
                <FileQuestion className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Нет вопросов</h3>
              <p className="text-muted-foreground text-center mb-4">
                Добавьте первый вопрос в этот тест
              </p>
              <Button onClick={handleCreateClick}>
                <Plus className="mr-2 h-4 w-4" />
                Добавить вопрос
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {sortedQuestions.map((question) => (
              <QuestionCard
                key={question.id}
                question={question}
                onEdit={() => handleEditClick(question)}
                onDelete={() => handleDelete(question)}
              />
            ))}
          </div>
        )}

        <QuestionDialog
          open={dialogOpen}
          onOpenChange={setDialogOpen}
          question={editingQuestion}
          nextOrder={questions.length}
          onSubmit={handleSubmit}
          isLoading={createQuestion.isPending || updateQuestion.isPending}
        />
      </div>
    </RoleGuard>
  );
}
