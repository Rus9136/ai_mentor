'use client';

import { useParams, useRouter } from 'next/navigation';
import { useTranslations, useLocale } from 'next-intl';
import Link from 'next/link';
import {
  ArrowLeft,
  Loader2,
  Calendar,
  Users,
  BarChart3,
  Edit,
  Send,
  Lock,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { HomeworkStatusBadge, QuestionCard } from '@/components/homework';
import { useHomework, usePublishHomework, useCloseHomework } from '@/lib/hooks/use-homework';
import { HomeworkStatus } from '@/types/homework';

export default function HomeworkDetailPage() {
  const params = useParams();
  const router = useRouter();
  const locale = useLocale();
  const t = useTranslations('homework');
  const tCommon = useTranslations('common');

  const homeworkId = Number(params.id);

  const { data: homework, isLoading, error } = useHomework(homeworkId);
  const publishMutation = usePublishHomework();
  const closeMutation = useCloseHomework();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !homework) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-destructive">{t('errors.loadFailed')}</p>
      </div>
    );
  }

  const handlePublish = () => {
    publishMutation.mutate({ homeworkId }, {
      onSuccess: () => {
        // Optionally show success notification
      },
    });
  };

  const handleClose = () => {
    closeMutation.mutate(homeworkId);
  };

  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString(locale === 'kz' ? 'kk-KZ' : 'ru-RU', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href={`/${locale}/homework`}>
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{homework.title}</h1>
            <HomeworkStatusBadge status={homework.status} />
          </div>
          {homework.class_name && (
            <p className="text-muted-foreground">{homework.class_name}</p>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          {homework.status === HomeworkStatus.DRAFT && (
            <>
              <Link href={`/${locale}/homework/${homeworkId}/edit`}>
                <Button variant="outline">
                  <Edit className="h-4 w-4 mr-2" />
                  {t('actions.edit')}
                </Button>
              </Link>
              <Button
                onClick={handlePublish}
                disabled={publishMutation.isPending || homework.tasks.length === 0}
              >
                {publishMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <Send className="h-4 w-4 mr-2" />
                )}
                {t('actions.publish')}
              </Button>
            </>
          )}
          {homework.status === HomeworkStatus.PUBLISHED && (
            <Button
              variant="destructive"
              onClick={handleClose}
              disabled={closeMutation.isPending}
            >
              {closeMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <Lock className="h-4 w-4 mr-2" />
              )}
              {t('actions.close')}
            </Button>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">{t('stats.totalStudents')}</span>
            </div>
            <p className="text-2xl font-bold mt-1">{homework.total_students}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <Send className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">{t('stats.submitted')}</span>
            </div>
            <p className="text-2xl font-bold mt-1">{homework.submitted_count}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">{t('stats.graded')}</span>
            </div>
            <p className="text-2xl font-bold mt-1">{homework.graded_count}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">{t('card.dueDate')}</span>
            </div>
            <p className="text-sm font-medium mt-1">{formatDate(homework.due_date)}</p>
          </CardContent>
        </Card>
      </div>

      {/* Description */}
      {homework.description && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t('form.description')}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{homework.description}</p>
          </CardContent>
        </Card>
      )}

      {/* Tasks and Questions */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold">{t('task.title')}</h2>
        {homework.tasks.length > 0 ? (
          homework.tasks.map((task, taskIndex) => (
            <Card key={task.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">
                    {taskIndex + 1}. {task.paragraph_title || task.chapter_title || t(`task.types.${task.task_type}`)}
                  </CardTitle>
                  <span className="text-sm text-muted-foreground">
                    {task.points} {t('task.points')}
                  </span>
                </div>
                {task.instructions && (
                  <p className="text-sm text-muted-foreground">{task.instructions}</p>
                )}
              </CardHeader>
              <CardContent>
                {task.questions.length > 0 ? (
                  <div className="space-y-3">
                    {task.questions.map((question, qIndex) => (
                      <QuestionCard
                        key={question.id}
                        question={question}
                        index={qIndex}
                        showAnswer={true}
                      />
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">{t('question.noQuestions')}</p>
                )}
              </CardContent>
            </Card>
          ))
        ) : (
          <Card>
            <CardContent className="py-8 text-center">
              <p className="text-muted-foreground">{t('task.noTasks')}</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
