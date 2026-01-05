'use client';

import { useTranslations } from 'next-intl';
import Link from 'next/link';
import { useLocale } from 'next-intl';
import { Calendar, Users, FileText, Sparkles } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { HomeworkStatusBadge } from './HomeworkStatusBadge';
import type { HomeworkListResponse } from '@/types/homework';

interface HomeworkCardProps {
  homework: HomeworkListResponse;
}

export function HomeworkCard({ homework }: HomeworkCardProps) {
  const t = useTranslations('homework');
  const locale = useLocale();

  const dueDate = new Date(homework.due_date);
  const isOverdue = dueDate < new Date() && homework.status === 'published';

  const formatDate = (date: Date) => {
    return date.toLocaleDateString(locale === 'kz' ? 'kk-KZ' : 'ru-RU', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-lg font-semibold line-clamp-2">
            {homework.title}
          </CardTitle>
          <HomeworkStatusBadge status={homework.status} />
        </div>
        {homework.class_name && (
          <p className="text-sm text-muted-foreground">{homework.class_name}</p>
        )}
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap gap-3 text-sm text-muted-foreground">
          <div className="flex items-center gap-1">
            <FileText className="h-4 w-4" />
            <span>{homework.tasks_count} {t('card.tasks')}</span>
          </div>
          <div className="flex items-center gap-1">
            <Users className="h-4 w-4" />
            <span>
              {homework.submitted_count}/{homework.total_students} {t('card.submitted')}
            </span>
          </div>
          {homework.ai_generation_enabled && (
            <div className="flex items-center gap-1 text-primary">
              <Sparkles className="h-4 w-4" />
              <span>{t('card.aiEnabled')}</span>
            </div>
          )}
        </div>

        <div className={`flex items-center gap-1 text-sm ${isOverdue ? 'text-destructive' : 'text-muted-foreground'}`}>
          <Calendar className="h-4 w-4" />
          <span>{t('card.dueDate')}: {formatDate(dueDate)}</span>
        </div>

        <div className="pt-2">
          <Link href={`/${locale}/homework/${homework.id}`}>
            <Button variant="outline" size="sm" className="w-full">
              {t('common.view', { defaultValue: 'Открыть' })}
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
