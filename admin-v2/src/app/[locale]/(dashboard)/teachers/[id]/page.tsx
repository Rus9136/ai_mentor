'use client';

import { use } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { ArrowLeft, Edit, Mail, Phone, BookOpen, Hash } from 'lucide-react';
import { format } from 'date-fns';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { RoleGuard } from '@/components/auth';
import { useTeacher } from '@/lib/hooks';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function TeacherDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const teacherId = parseInt(id);
  const t = useTranslations('teachers');
  const router = useRouter();
  const locale = 'ru';

  const { data: teacher, isLoading } = useTeacher(teacherId);

  if (isLoading) {
    return (
      <RoleGuard allowedRoles={['admin']}>
        <div className="space-y-6">
          <div className="flex items-center gap-4">
            <Skeleton className="h-10 w-10" />
            <Skeleton className="h-10 w-64" />
          </div>
          <Card>
            <CardHeader>
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-4 w-32" />
            </CardHeader>
            <CardContent className="space-y-4">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
            </CardContent>
          </Card>
        </div>
      </RoleGuard>
    );
  }

  if (!teacher) {
    return (
      <RoleGuard allowedRoles={['admin']}>
        <div className="flex flex-col items-center justify-center py-12">
          <p className="text-muted-foreground">Учитель не найден</p>
          <Button variant="link" onClick={() => router.back()}>
            Вернуться назад
          </Button>
        </div>
      </RoleGuard>
    );
  }

  const user = teacher.user;
  const fullName = user
    ? `${user.last_name || ''} ${user.first_name || ''} ${user.middle_name || ''}`.trim()
    : 'Нет данных';

  return (
    <RoleGuard allowedRoles={['admin']}>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => router.back()}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">{fullName}</h1>
              {teacher.subject && (
                <p className="text-muted-foreground">{teacher.subject}</p>
              )}
            </div>
          </div>
          <Button onClick={() => router.push(`/${locale}/teachers/${teacher.id}/edit`)}>
            <Edit className="mr-2 h-4 w-4" />
            {t('edit')}
          </Button>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Личные данные</CardTitle>
              <CardDescription>Основная информация об учителе</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3">
                <Mail className="h-4 w-4 text-muted-foreground" />
                <span>{user?.email || '—'}</span>
              </div>
              {user?.phone && (
                <div className="flex items-center gap-3">
                  <Phone className="h-4 w-4 text-muted-foreground" />
                  <span>{user.phone}</span>
                </div>
              )}
              {teacher.subject && (
                <div className="flex items-center gap-3">
                  <BookOpen className="h-4 w-4 text-muted-foreground" />
                  <span>Предмет: {teacher.subject}</span>
                </div>
              )}
              {teacher.teacher_code && (
                <div className="flex items-center gap-3">
                  <Hash className="h-4 w-4 text-muted-foreground" />
                  <span>Код: {teacher.teacher_code}</span>
                </div>
              )}

              <Separator />

              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Статус:</span>
                <Badge variant={user?.is_active ? 'default' : 'secondary'}>
                  {user?.is_active ? 'Активен' : 'Неактивен'}
                </Badge>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Классы</CardTitle>
              <CardDescription>Закрепленные классы</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {teacher.classes && teacher.classes.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {teacher.classes.map((cls) => (
                    <Badge key={cls.id} variant="secondary">
                      {cls.name} ({cls.academic_year})
                    </Badge>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">
                  Нет закрепленных классов
                </p>
              )}

              {teacher.bio && (
                <>
                  <Separator />
                  <div>
                    <span className="text-sm font-medium">Биография:</span>
                    <p className="mt-1 text-sm text-muted-foreground">{teacher.bio}</p>
                  </div>
                </>
              )}

              <Separator />

              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Добавлен:</span>
                <span>
                  {format(new Date(teacher.created_at), 'dd.MM.yyyy HH:mm')}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </RoleGuard>
  );
}
