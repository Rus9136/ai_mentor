'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { AlertTriangle, Loader2, Sparkles } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import type { AnswerForReview, TeacherReviewRequest } from '@/types/homework';

interface ReviewAnswerCardProps {
  answer: AnswerForReview;
  onReview: (data: TeacherReviewRequest) => void;
  isSubmitting?: boolean;
}

export function ReviewAnswerCard({ answer, onReview, isSubmitting }: ReviewAnswerCardProps) {
  const t = useTranslations('homework.review');

  const [score, setScore] = useState<number>(
    answer.ai_score ? Math.round(answer.ai_score * 100) : 0
  );
  const [feedback, setFeedback] = useState(answer.ai_feedback || '');

  const confidencePercent = answer.ai_confidence ? Math.round(answer.ai_confidence * 100) : 0;
  const isLowConfidence = confidencePercent < 70;

  const handleSubmit = () => {
    onReview({
      score,
      feedback: feedback || undefined,
    });
  };

  return (
    <Card className={isLowConfidence ? 'border-amber-300 dark:border-amber-700' : undefined}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div>
            <CardTitle className="text-base">{answer.student_name}</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              {new Date(answer.submitted_at).toLocaleString()}
            </p>
          </div>
          {isLowConfidence && (
            <Badge variant="warning" className="flex items-center gap-1">
              <AlertTriangle className="h-3 w-3" />
              {t('lowConfidence')}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Question */}
        <div className="space-y-1">
          <Label className="text-muted-foreground text-xs">Вопрос</Label>
          <p className="text-sm bg-muted/50 p-2 rounded-md">{answer.question_text}</p>
        </div>

        {/* Student Answer */}
        <div className="space-y-1">
          <Label className="text-muted-foreground text-xs">Ответ ученика</Label>
          <p className="text-sm bg-muted/50 p-3 rounded-md whitespace-pre-wrap">
            {answer.answer_text || '—'}
          </p>
        </div>

        {/* Expected Answer Hints */}
        {answer.expected_answer_hints && (
          <div className="space-y-1">
            <Label className="text-muted-foreground text-xs">Ожидаемый ответ</Label>
            <p className="text-sm text-muted-foreground bg-blue-50 dark:bg-blue-950 p-2 rounded-md">
              {answer.expected_answer_hints}
            </p>
          </div>
        )}

        {/* AI Assessment */}
        {answer.ai_score !== null && answer.ai_score !== undefined && (
          <div className="p-3 bg-muted/30 rounded-md space-y-2">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium">AI оценка</span>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-muted-foreground mb-1">{t('aiScore')}</p>
                <p className="text-lg font-semibold">
                  {Math.round(answer.ai_score * 100)}%
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">{t('confidence')}</p>
                <div className="flex items-center gap-2">
                  <Progress value={confidencePercent} className="h-2 flex-1" />
                  <span className="text-sm">{confidencePercent}%</span>
                </div>
              </div>
            </div>
            {answer.ai_feedback && (
              <p className="text-sm text-muted-foreground mt-2">{answer.ai_feedback}</p>
            )}
          </div>
        )}

        {/* Teacher Review Form */}
        <div className="space-y-3 pt-2 border-t">
          <div className="space-y-2">
            <Label htmlFor="score">{t('yourScore')} (0-100)</Label>
            <Input
              id="score"
              type="number"
              min={0}
              max={100}
              value={score}
              onChange={(e) => setScore(Number(e.target.value))}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="feedback">{t('feedback')}</Label>
            <Textarea
              id="feedback"
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder={t('feedbackPlaceholder')}
              rows={3}
            />
          </div>

          <Button onClick={handleSubmit} disabled={isSubmitting} className="w-full">
            {isSubmitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                {t('submitting')}
              </>
            ) : (
              t('submit')
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
