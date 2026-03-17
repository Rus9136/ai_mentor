'use client';

import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Edit, FileQuestion } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useTeacherTest } from '@/lib/hooks/use-teacher-tests';
import type { DifficultyLevel, TestPurpose } from '@/types/test';

const difficultyLabels: Record<DifficultyLevel, string> = {
  easy: 'Легкий',
  medium: 'Средний',
  hard: 'Сложный',
};

const purposeLabels: Record<TestPurpose, string> = {
  diagnostic: 'Диагностический',
  formative: 'Формативный',
  summative: 'Суммативный',
  practice: 'Практический',
};

export default function TeacherTestDetailPage() {
  const params = useParams();
  const router = useRouter();
  const locale = 'ru';
  const testId = Number(params.id);

  const { data: test, isLoading } = useTeacherTest(testId);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-muted animate-pulse rounded" />
        <div className="h-[300px] w-full bg-muted animate-pulse rounded" />
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

  const isSchoolTest = test.school_id !== null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.push(`/${locale}/tests`)}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-3xl font-bold tracking-tight">{test.title}</h1>
              <Badge variant={test.is_active ? 'default' : 'secondary'}>
                {test.is_active ? 'Активен' : 'Неактивен'}
              </Badge>
              {!isSchoolTest && (
                <Badge variant="outline">Глобальный</Badge>
              )}
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => router.push(`/${locale}/tests/${testId}/questions`)}
          >
            <FileQuestion className="mr-2 h-4 w-4" />
            Вопросы
          </Button>
          {isSchoolTest && (
            <Button onClick={() => router.push(`/${locale}/tests/${testId}/edit`)}>
              <Edit className="mr-2 h-4 w-4" />
              Редактировать
            </Button>
          )}
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Основная информация</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-muted-foreground">Название</p>
              <p className="font-medium">{test.title}</p>
            </div>
            {test.description && (
              <div>
                <p className="text-sm text-muted-foreground">Описание</p>
                <p>{test.description}</p>
              </div>
            )}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Назначение</p>
                <Badge variant="outline">{purposeLabels[test.test_purpose]}</Badge>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Сложность</p>
                <Badge>{difficultyLabels[test.difficulty]}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Параметры</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Ограничение по времени</p>
                <p className="font-medium">
                  {test.time_limit ? `${test.time_limit} мин` : 'Без ограничения'}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Проходной балл</p>
                <p className="font-medium">{test.passing_score}%</p>
              </div>
            </div>
            {test.textbook_title && (
              <div>
                <p className="text-sm text-muted-foreground">Учебник</p>
                <p className="font-medium">{test.textbook_title}</p>
              </div>
            )}
            {test.chapter_title && (
              <div>
                <p className="text-sm text-muted-foreground">Глава</p>
                <p className="font-medium">{test.chapter_title}</p>
              </div>
            )}
            {test.paragraph_title && (
              <div>
                <p className="text-sm text-muted-foreground">Параграф</p>
                <p className="font-medium">{test.paragraph_title}</p>
              </div>
            )}
            <div>
              <p className="text-sm text-muted-foreground">Дата создания</p>
              <p className="font-medium">
                {new Date(test.created_at).toLocaleDateString('ru-RU')}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
