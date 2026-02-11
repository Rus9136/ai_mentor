'use client';

import { useState } from 'react';
import { Plus, Pencil, Trash2, Loader2, CheckCircle2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  useEmbeddedQuestions,
  useCreateEmbeddedQuestion,
  useUpdateEmbeddedQuestion,
  useDeleteEmbeddedQuestion,
} from '@/lib/hooks/use-embedded-questions';
import type { EmbeddedQuestion, EmbeddedQuestionCreate, EmbeddedQuestionUpdate } from '@/types';
import type { EmbeddedQuestionInput } from '@/lib/validations/embedded-question';
import { EmbeddedQuestionDialog } from './embedded-question-dialog';

interface EmbeddedQuestionsSectionProps {
  paragraphId: number;
  isSchool?: boolean;
}

const TYPE_LABELS: Record<string, string> = {
  single_choice: 'Один ответ',
  multiple_choice: 'Несколько',
  true_false: 'Верно/Неверно',
};

const TYPE_VARIANTS: Record<string, 'default' | 'secondary' | 'outline'> = {
  single_choice: 'default',
  multiple_choice: 'secondary',
  true_false: 'outline',
};

export function EmbeddedQuestionsSection({
  paragraphId,
  isSchool = false,
}: EmbeddedQuestionsSectionProps) {
  const { data: questions = [], isLoading } = useEmbeddedQuestions(paragraphId, isSchool);
  const createMutation = useCreateEmbeddedQuestion(isSchool);
  const updateMutation = useUpdateEmbeddedQuestion(isSchool);
  const deleteMutation = useDeleteEmbeddedQuestion(isSchool);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedQuestion, setSelectedQuestion] = useState<EmbeddedQuestion | undefined>();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [questionToDelete, setQuestionToDelete] = useState<EmbeddedQuestion | null>(null);

  const handleAdd = () => {
    setSelectedQuestion(undefined);
    setDialogOpen(true);
  };

  const handleEdit = (q: EmbeddedQuestion) => {
    setSelectedQuestion(q);
    setDialogOpen(true);
  };

  const handleDelete = (q: EmbeddedQuestion) => {
    setQuestionToDelete(q);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (questionToDelete) {
      deleteMutation.mutate({
        id: questionToDelete.id,
        paragraphId,
      });
    }
    setDeleteDialogOpen(false);
    setQuestionToDelete(null);
  };

  const handleSubmit = (data: EmbeddedQuestionInput) => {
    if (selectedQuestion) {
      const updateData: EmbeddedQuestionUpdate = { ...data };
      updateMutation.mutate(
        { id: selectedQuestion.id, paragraphId, data: updateData },
        { onSuccess: () => setDialogOpen(false) }
      );
    } else {
      const createData: EmbeddedQuestionCreate = {
        ...data,
        paragraph_id: paragraphId,
      };
      createMutation.mutate(createData, {
        onSuccess: () => setDialogOpen(false),
      });
    }
  };

  return (
    <>
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" />
              Встроенные вопросы &quot;Проверь себя&quot;
            </CardTitle>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleAdd}
            >
              <Plus className="h-4 w-4 mr-1" />
              Добавить
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-2">
          {isLoading ? (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : questions.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">
              Нет встроенных вопросов. Нажмите &quot;Добавить&quot; для создания.
            </p>
          ) : (
            questions.map((q) => (
              <div
                key={q.id}
                className="flex items-center justify-between p-3 rounded-md border bg-background"
              >
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <span className="text-sm font-medium text-muted-foreground flex-shrink-0">
                    #{q.sort_order}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm truncate">{q.question_text}</p>
                  </div>
                  <Badge variant={TYPE_VARIANTS[q.question_type] || 'outline'} className="flex-shrink-0">
                    {TYPE_LABELS[q.question_type] || q.question_type}
                  </Badge>
                </div>
                <div className="flex items-center gap-1 ml-2 flex-shrink-0">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => handleEdit(q)}
                  >
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDelete(q)}
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      <EmbeddedQuestionDialog
        open={dialogOpen}
        onOpenChange={(open) => {
          setDialogOpen(open);
          if (!open) setSelectedQuestion(undefined);
        }}
        question={selectedQuestion}
        nextOrder={questions.length}
        onSubmit={handleSubmit}
        isLoading={createMutation.isPending || updateMutation.isPending}
      />

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Удалить вопрос?</AlertDialogTitle>
            <AlertDialogDescription>
              Вы уверены, что хотите удалить этот встроенный вопрос?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Удалить
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
