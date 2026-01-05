'use client';

import { useTranslations } from 'next-intl';
import { Sparkles, Check, X } from 'lucide-react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { QuestionResponse, QuestionResponseWithAnswer } from '@/types/homework';

interface QuestionCardProps {
  question: QuestionResponse | QuestionResponseWithAnswer;
  index: number;
  showAnswer?: boolean;
}

export function QuestionCard({ question, index, showAnswer = false }: QuestionCardProps) {
  const t = useTranslations('homework.question');

  const getDifficultyColor = (difficulty?: string) => {
    switch (difficulty) {
      case 'easy':
        return 'success';
      case 'medium':
        return 'warning';
      case 'hard':
        return 'destructive';
      default:
        return 'secondary';
    }
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="font-medium text-muted-foreground">#{index + 1}</span>
            <Badge variant="outline" className="text-xs">
              {t(`types.${question.question_type}`)}
            </Badge>
            {question.difficulty && (
              <Badge variant={getDifficultyColor(question.difficulty) as any} className="text-xs">
                {question.difficulty}
              </Badge>
            )}
            {question.bloom_level && (
              <Badge variant="secondary" className="text-xs">
                {t(`bloomLevels.${question.bloom_level}`)}
              </Badge>
            )}
          </div>
          {question.ai_generated && (
            <Badge variant="info" className="text-xs">
              <Sparkles className="h-3 w-3 mr-1" />
              {t('aiGenerated')}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm">{question.question_text}</p>

        {/* Options for choice questions */}
        {question.options && question.options.length > 0 && (
          <div className="space-y-2">
            {question.options.map((option, i) => (
              <div
                key={option.id}
                className={`flex items-center gap-2 p-2 rounded-md text-sm ${
                  showAnswer && option.is_correct
                    ? 'bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800'
                    : 'bg-muted/50'
                }`}
              >
                <span className="font-medium text-muted-foreground w-6">
                  {String.fromCharCode(65 + i)}.
                </span>
                <span className="flex-1">{option.text}</span>
                {showAnswer && option.is_correct && (
                  <Check className="h-4 w-4 text-green-600" />
                )}
              </div>
            ))}
          </div>
        )}

        {/* Correct answer for short answer */}
        {showAnswer && 'correct_answer' in question && question.correct_answer && (
          <div className="p-2 bg-green-50 dark:bg-green-950 rounded-md border border-green-200 dark:border-green-800">
            <p className="text-sm">
              <span className="font-medium text-green-700 dark:text-green-300">Ответ: </span>
              {question.correct_answer}
            </p>
          </div>
        )}

        {/* Explanation */}
        {showAnswer && question.explanation && (
          <div className="p-2 bg-blue-50 dark:bg-blue-950 rounded-md border border-blue-200 dark:border-blue-800">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              {question.explanation}
            </p>
          </div>
        )}

        {/* Points */}
        <div className="text-xs text-muted-foreground">
          {question.points} балл(ов)
        </div>
      </CardContent>
    </Card>
  );
}
