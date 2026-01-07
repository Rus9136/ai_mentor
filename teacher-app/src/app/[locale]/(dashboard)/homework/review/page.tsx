'use client';

import { useTranslations } from 'next-intl';
import { Loader2, CheckCircle2 } from 'lucide-react';
import { ReviewAnswerCard } from '@/components/homework';
import { useReviewQueue, useReviewAnswer } from '@/lib/hooks/use-homework';

export default function ReviewQueuePage() {
  const t = useTranslations('homework.review');

  const { data: answers, isLoading, error } = useReviewQueue();
  const reviewMutation = useReviewAnswer();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-destructive">{t('errors.loadFailed', { defaultValue: 'Ошибка загрузки' })}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t('title')}</h1>
        {answers && answers.length > 0 && (
          <p className="text-muted-foreground">
            {answers.length} ответ(ов) на проверке
          </p>
        )}
      </div>

      {/* Review Cards */}
      {answers && answers.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {answers.map((answer) => (
            <ReviewAnswerCard
              key={answer.id}
              answer={answer}
              onReview={(data) =>
                reviewMutation.mutate({ answerId: answer.id, data })
              }
              isSubmitting={reviewMutation.isPending}
            />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <CheckCircle2 className="h-12 w-12 text-green-500 mb-4" />
          <h3 className="text-lg font-medium mb-1">{t('allReviewed')}</h3>
          <p className="text-muted-foreground">{t('noAnswers')}</p>
        </div>
      )}
    </div>
  );
}
