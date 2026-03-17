'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Plus, FileQuestion } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { QuestionCard } from '@/components/tests/question-card';
import { QuestionDialog } from '@/components/tests/question-dialog';
import {
  useTeacherTest,
  useTeacherTestQuestions,
  useCreateTeacherQuestion,
  useUpdateTeacherQuestion,
  useDeleteTeacherQuestion,
} from '@/lib/hooks/use-teacher-tests';
import type { Question, QuestionCreate } from '@/types/test';

export default function TeacherQuestionsPage() {
  const params = useParams();
  const router = useRouter();
  const locale = 'ru';
  const testId = Number(params.id);

  const { data: test, isLoading: testLoading } = useTeacherTest(testId);
  const { data: questionsData, isLoading: questionsLoading } = useTeacherTestQuestions(testId);
  const createQuestion = useCreateTeacherQuestion();
  const updateQuestion = useUpdateTeacherQuestion();
  const deleteQuestion = useDeleteTeacherQuestion();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState<Question | undefined>();

  const questions = questionsData?.items ?? [];
  const isSchoolTest = test?.school_id !== null;

  const handleCreateClick = () => {
    setEditingQuestion(undefined);
    setDialogOpen(true);
  };

  const handleEditClick = (question: Question) => {
    setEditingQuestion(question);
    setDialogOpen(true);
  };

  const handleDelete = (question: Question) => {
    deleteQuestion.mutate({ questionId: question.id, testId });
  };

  const handleSubmit = (data: QuestionCreate) => {
    if (editingQuestion) {
      updateQuestion.mutate(
        { questionId: editingQuestion.id, testId, data },
        { onSuccess: () => { setDialogOpen(false); setEditingQuestion(undefined); } }
      );
    } else {
      createQuestion.mutate(
        { testId, data },
        { onSuccess: () => { setDialogOpen(false); } }
      );
    }
  };

  const isLoading = testLoading || questionsLoading;

  const sortedQuestions = [...questions].sort((a, b) => a.sort_order - b.sort_order);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-muted animate-pulse rounded" />
        <div className="space-y-4">
          <div className="h-40 w-full bg-muted animate-pulse rounded" />
          <div className="h-40 w-full bg-muted animate-pulse rounded" />
        </div>
      </div>
    );
  }

  if (!test) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Тест не найден</p>
        <Button variant="link" onClick={() => router.push(`/${locale}/tests`)}>
          Вернуться к списку
        </Button>
      </div>
    );
  }

  return (
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
            <h1 className="text-3xl font-bold tracking-tight">Вопросы</h1>
            <p className="text-muted-foreground">
              {test.title} &bull; {questions.length} вопросов
            </p>
          </div>
        </div>
        {isSchoolTest && (
          <Button onClick={handleCreateClick}>
            <Plus className="mr-2 h-4 w-4" />
            Добавить вопрос
          </Button>
        )}
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
            {isSchoolTest && (
              <Button onClick={handleCreateClick}>
                <Plus className="mr-2 h-4 w-4" />
                Добавить вопрос
              </Button>
            )}
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
              readOnly={!isSchoolTest}
            />
          ))}
        </div>
      )}

      {isSchoolTest && (
        <QuestionDialog
          open={dialogOpen}
          onOpenChange={setDialogOpen}
          question={editingQuestion}
          nextOrder={questions.length}
          onSubmit={handleSubmit}
          isLoading={createQuestion.isPending || updateQuestion.isPending}
        />
      )}
    </div>
  );
}
