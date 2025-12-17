'use client';

import { use } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { ArrowLeft, Edit, Mail, Phone, Calendar, Hash } from 'lucide-react';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

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
import { useStudent } from '@/lib/hooks';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function StudentDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const studentId = parseInt(id);
  const t = useTranslations('students');
  const router = useRouter();
  const locale = 'ru';

  const { data: student, isLoading } = useStudent(studentId);

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
              <Skeleton className="h-4 w-1/2" />
            </CardContent>
          </Card>
        </div>
      </RoleGuard>
    );
  }

  if (!student) {
    return (
      <RoleGuard allowedRoles={['admin']}>
        <div className="flex flex-col items-center justify-center py-12">
          <p className="text-muted-foreground">Ученик не найден</p>
          <Button variant="link" onClick={() => router.back()}>
            Вернуться назад
          </Button>
        </div>
      </RoleGuard>
    );
  }

  const user = student.user;
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
              <p className="text-muted-foreground">
                {student.grade_level} класс
              </p>
            </div>
          </div>
          <Button onClick={() => router.push(`/${locale}/students/${student.id}/edit`)}>
            <Edit className="mr-2 h-4 w-4" />
            {t('edit')}
          </Button>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Личные данные</CardTitle>
              <CardDescription>Основная информация об ученике</CardDescription>
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
              {student.birth_date && (
                <div className="flex items-center gap-3">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span>
                    Дата рождения:{' '}
                    {format(new Date(student.birth_date), 'dd MMMM yyyy', { locale: ru })}
                  </span>
                </div>
              )}
              {student.student_code && (
                <div className="flex items-center gap-3">
                  <Hash className="h-4 w-4 text-muted-foreground" />
                  <span>Код: {student.student_code}</span>
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
              <CardTitle>Обучение</CardTitle>
              <CardDescription>Информация об обучении</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Класс:</span>
                <Badge variant="outline">{student.grade_level} класс</Badge>
              </div>

              {student.enrollment_date && (
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Дата зачисления:</span>
                  <span>
                    {format(new Date(student.enrollment_date), 'dd.MM.yyyy')}
                  </span>
                </div>
              )}

              {student.classes && student.classes.length > 0 && (
                <>
                  <Separator />
                  <div>
                    <span className="text-sm text-muted-foreground">Классы:</span>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {student.classes.map((cls) => (
                        <Badge key={cls.id} variant="secondary">
                          {cls.name}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </>
              )}

              <Separator />

              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Добавлен:</span>
                <span>
                  {format(new Date(student.created_at), 'dd.MM.yyyy HH:mm')}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </RoleGuard>
  );
}
