'use client';

import { useParams, useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import {
  ArrowLeft,
  Pencil,
  BookOpen,
  CheckCircle,
  XCircle,
  Calendar,
  User,
  Building2,
  Globe,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import { RoleGuard } from '@/components/auth';
import { useTextbook } from '@/lib/hooks/use-textbooks';

export default function TextbookShowPage() {
  const t = useTranslations('textbooks');
  const params = useParams();
  const router = useRouter();
  const textbookId = Number(params.id);

  const { data: textbook, isLoading } = useTextbook(textbookId, false);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10" />
          <Skeleton className="h-8 w-48" />
        </div>
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
          </CardHeader>
          <CardContent className="space-y-4">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!textbook) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <p className="text-muted-foreground">Учебник не найден</p>
        <Button variant="link" onClick={() => router.back()}>
          Вернуться назад
        </Button>
      </div>
    );
  }

  return (
    <RoleGuard allowedRoles={['super_admin']}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => router.back()}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-3xl font-bold tracking-tight">
                  {textbook.title}
                </h1>
                <Badge variant={textbook.is_active ? 'default' : 'secondary'}>
                  {textbook.is_active ? (
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
                <Badge variant="outline">
                  {textbook.school_id === null ? (
                    <>
                      <Globe className="mr-1 h-3 w-3" />
                      Глобальный
                    </>
                  ) : (
                    <>
                      <Building2 className="mr-1 h-3 w-3" />
                      Школьный
                    </>
                  )}
                </Badge>
              </div>
              <p className="text-muted-foreground">
                {textbook.subject} • {textbook.grade_level} класс
              </p>
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => router.push(`/ru/textbooks/${textbook.id}/structure`)}
            >
              <BookOpen className="mr-2 h-4 w-4" />
              {t('structure')}
            </Button>
            <Button onClick={() => router.push(`/ru/textbooks/${textbook.id}/edit`)}>
              <Pencil className="mr-2 h-4 w-4" />
              {t('edit')}
            </Button>
          </div>
        </div>

        {/* Content */}
        <div className="grid gap-6 md:grid-cols-2">
          {/* Main Info */}
          <Card>
            <CardHeader>
              <CardTitle>Основная информация</CardTitle>
              <CardDescription>Данные учебника</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {textbook.author && (
                <div className="flex items-center gap-3">
                  <User className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <p className="text-sm font-medium">Автор</p>
                    <p className="text-sm text-muted-foreground">
                      {textbook.author}
                    </p>
                  </div>
                </div>
              )}

              {textbook.publisher && (
                <div className="flex items-center gap-3">
                  <Building2 className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <p className="text-sm font-medium">Издательство</p>
                    <p className="text-sm text-muted-foreground">
                      {textbook.publisher}
                    </p>
                  </div>
                </div>
              )}

              {textbook.year && (
                <div className="flex items-center gap-3">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <p className="text-sm font-medium">Год издания</p>
                    <p className="text-sm text-muted-foreground">
                      {textbook.year}
                    </p>
                  </div>
                </div>
              )}

              {textbook.isbn && (
                <div>
                  <p className="text-sm font-medium">ISBN</p>
                  <code className="text-sm text-muted-foreground">
                    {textbook.isbn}
                  </code>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Metadata */}
          <Card>
            <CardHeader>
              <CardTitle>Метаданные</CardTitle>
              <CardDescription>Системная информация</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm font-medium">Версия</p>
                <p className="text-sm text-muted-foreground">v{textbook.version}</p>
              </div>

              <Separator />

              <div className="flex items-center gap-3">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">Дата создания</p>
                  <p className="text-sm text-muted-foreground">
                    {format(new Date(textbook.created_at), 'dd MMMM yyyy, HH:mm', {
                      locale: ru,
                    })}
                  </p>
                </div>
              </div>

              <Separator />

              <div className="flex items-center gap-3">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">Последнее обновление</p>
                  <p className="text-sm text-muted-foreground">
                    {format(new Date(textbook.updated_at), 'dd MMMM yyyy, HH:mm', {
                      locale: ru,
                    })}
                  </p>
                </div>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium">ID</p>
                <p className="text-sm text-muted-foreground">{textbook.id}</p>
              </div>
            </CardContent>
          </Card>

          {/* Description */}
          {textbook.description && (
            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle>Описание</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="whitespace-pre-wrap">{textbook.description}</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </RoleGuard>
  );
}
