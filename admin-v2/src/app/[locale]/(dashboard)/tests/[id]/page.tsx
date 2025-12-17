'use client';

import { useParams, useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import {
  ArrowLeft,
  Edit,
  ClipboardList,
  Timer,
  Target,
  Calendar,
  CheckCircle,
  XCircle,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { RoleGuard } from '@/components/auth';
import { useTest } from '@/lib/hooks/use-tests';
import type { TestPurpose, DifficultyLevel } from '@/types';

const PURPOSE_LABELS: Record<TestPurpose, string> = {
  diagnostic: 'Диагностический',
  formative: 'Формативный',
  summative: 'Суммативный',
  practice: 'Практический',
};

const DIFFICULTY_LABELS: Record<DifficultyLevel, string> = {
  easy: 'Легкий',
  medium: 'Средний',
  hard: 'Сложный',
};

const DIFFICULTY_COLORS: Record<DifficultyLevel, string> = {
  easy: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  hard: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
};

export default function TestShowPage() {
  const params = useParams();
  const router = useRouter();
  const t = useTranslations('tests');
  const locale = 'ru';

  const testId = Number(params.id);
  const { data: test, isLoading } = useTest(testId, false); // global test

  if (isLoading) {
    return (
      <RoleGuard allowedRoles={['super_admin']}>
        <div className="space-y-6">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-[400px] w-full" />
        </div>
      </RoleGuard>
    );
  }

  if (!test) {
    return (
      <RoleGuard allowedRoles={['super_admin']}>
        <div className="text-center py-12">
          <p className="text-muted-foreground">Тест не найден</p>
          <Button
            variant="link"
            onClick={() => router.push(`/${locale}/tests`)}
          >
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
              onClick={() => router.push(`/${locale}/tests`)}
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-3xl font-bold tracking-tight">{test.title}</h1>
                <Badge variant={test.is_active ? 'default' : 'secondary'}>
                  {test.is_active ? (
                    <>
                      <CheckCircle className="mr-1 h-3 w-3" />
                      Активен
                    </>
                  ) : (
                    <>
                      <XCircle className="mr-1 h-3 w-3" />
                      Неактивен
                    </>
                  )}
                </Badge>
              </div>
              <p className="text-muted-foreground">
                ID: {test.id} • Глобальный тест
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => router.push(`/${locale}/tests/${test.id}/questions`)}
            >
              <ClipboardList className="mr-2 h-4 w-4" />
              Вопросы
            </Button>
            <Button
              onClick={() => router.push(`/${locale}/tests/${test.id}/edit`)}
            >
              <Edit className="mr-2 h-4 w-4" />
              Редактировать
            </Button>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Основная информация</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="text-sm text-muted-foreground">Название</div>
                <div className="font-medium">{test.title}</div>
              </div>
              {test.description && (
                <div>
                  <div className="text-sm text-muted-foreground">Описание</div>
                  <div>{test.description}</div>
                </div>
              )}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-muted-foreground">Назначение</div>
                  <Badge variant="outline" className="mt-1">
                    {PURPOSE_LABELS[test.test_purpose]}
                  </Badge>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Сложность</div>
                  <Badge className={`mt-1 ${DIFFICULTY_COLORS[test.difficulty]}`}>
                    {DIFFICULTY_LABELS[test.difficulty]}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Параметры теста</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                  <Timer className="h-5 w-5 text-muted-foreground" />
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Лимит времени</div>
                  <div className="font-medium">
                    {test.time_limit ? `${test.time_limit} минут` : 'Без ограничения'}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                  <Target className="h-5 w-5 text-muted-foreground" />
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Проходной балл</div>
                  <div className="font-medium">{test.passing_score}%</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                  <Calendar className="h-5 w-5 text-muted-foreground" />
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Дата создания</div>
                  <div className="font-medium">
                    {format(new Date(test.created_at), 'dd MMMM yyyy, HH:mm', { locale: ru })}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {(test.chapter_id || test.paragraph_id) && (
          <Card>
            <CardHeader>
              <CardTitle>Привязка к контенту</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {test.chapter_id && (
                <div>
                  <span className="text-sm text-muted-foreground">Глава ID: </span>
                  <span className="font-medium">{test.chapter_id}</span>
                </div>
              )}
              {test.paragraph_id && (
                <div>
                  <span className="text-sm text-muted-foreground">Параграф ID: </span>
                  <span className="font-medium">{test.paragraph_id}</span>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </RoleGuard>
  );
}
