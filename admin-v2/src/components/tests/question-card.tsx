'use client';

import { useState } from 'react';
import {
  GripVertical,
  Edit,
  Trash2,
  CheckCircle,
  XCircle,
  HelpCircle,
} from 'lucide-react';

import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
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
import type { Question, QuestionType } from '@/types';

interface QuestionCardProps {
  question: Question;
  onEdit: () => void;
  onDelete: () => void;
}

const TYPE_LABELS: Record<QuestionType, string> = {
  single_choice: 'Один ответ',
  multiple_choice: 'Несколько ответов',
  true_false: 'Верно/Неверно',
  short_answer: 'Краткий ответ',
};

const TYPE_COLORS: Record<QuestionType, string> = {
  single_choice: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  multiple_choice: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  true_false: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  short_answer: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
};

export function QuestionCard({ question, onEdit, onDelete }: QuestionCardProps) {
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const correctOptions = question.options.filter((o) => o.is_correct);
  const incorrectOptions = question.options.filter((o) => !o.is_correct);

  return (
    <>
      <Card className="group hover:shadow-md transition-shadow">
        <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
          <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted text-sm font-medium">
              {question.sort_order + 1}
            </div>
            <div className="space-y-1">
              <Badge className={TYPE_COLORS[question.question_type]}>
                {TYPE_LABELS[question.question_type]}
              </Badge>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span>{question.points} {question.points === 1 ? 'балл' : 'баллов'}</span>
              </div>
            </div>
          </div>
          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button variant="ghost" size="icon" onClick={onEdit}>
              <Edit className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setDeleteDialogOpen(true)}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm">{question.question_text}</p>

          {question.options.length > 0 && (
            <div className="space-y-2">
              {question.options
                .sort((a, b) => a.sort_order - b.sort_order)
                .map((option) => (
                  <div
                    key={option.id}
                    className={`flex items-center gap-2 rounded-md p-2 text-sm ${
                      option.is_correct
                        ? 'bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800'
                        : 'bg-muted'
                    }`}
                  >
                    {option.is_correct ? (
                      <CheckCircle className="h-4 w-4 text-green-600 flex-shrink-0" />
                    ) : (
                      <XCircle className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                    )}
                    <span>{option.option_text}</span>
                  </div>
                ))}
            </div>
          )}

          {question.explanation && (
            <div className="flex items-start gap-2 rounded-md bg-muted p-3">
              <HelpCircle className="h-4 w-4 text-muted-foreground flex-shrink-0 mt-0.5" />
              <div className="text-sm text-muted-foreground">
                <span className="font-medium">Пояснение:</span> {question.explanation}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Удалить вопрос?</AlertDialogTitle>
            <AlertDialogDescription>
              Вы уверены, что хотите удалить этот вопрос? Это действие нельзя отменить.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction
              onClick={onDelete}
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
