'use client';

import { useParams, useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import {
  ArrowLeft,
  Pencil,
  Ban,
  CheckCircle,
  Mail,
  Phone,
  MapPin,
  Calendar,
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
import { useSchool, useBlockSchool, useUnblockSchool } from '@/lib/hooks/use-schools';

export default function SchoolShowPage() {
  const t = useTranslations('schools');
  const params = useParams();
  const router = useRouter();
  const schoolId = Number(params.id);

  const { data: school, isLoading } = useSchool(schoolId);
  const blockSchool = useBlockSchool();
  const unblockSchool = useUnblockSchool();

  const handleBlock = () => {
    if (school) {
      blockSchool.mutate(school.id);
    }
  };

  const handleUnblock = () => {
    if (school) {
      unblockSchool.mutate(school.id);
    }
  };

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
            <Skeleton className="h-4 w-1/2" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!school) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <p className="text-muted-foreground">Школа не найдена</p>
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
                  {school.name}
                </h1>
                <Badge variant={school.is_active ? 'default' : 'destructive'}>
                  {school.is_active ? (
                    <>
                      <CheckCircle className="mr-1 h-3 w-3" />
                      Активна
                    </>
                  ) : (
                    <>
                      <Ban className="mr-1 h-3 w-3" />
                      Заблокирована
                    </>
                  )}
                </Badge>
              </div>
              <p className="text-muted-foreground">
                <code className="rounded bg-muted px-1.5 py-0.5 text-sm">
                  {school.code}
                </code>
              </p>
            </div>
          </div>

          <div className="flex gap-2">
            {school.is_active ? (
              <Button
                variant="outline"
                onClick={handleBlock}
                disabled={blockSchool.isPending}
              >
                <Ban className="mr-2 h-4 w-4" />
                {t('block')}
              </Button>
            ) : (
              <Button
                variant="outline"
                onClick={handleUnblock}
                disabled={unblockSchool.isPending}
              >
                <CheckCircle className="mr-2 h-4 w-4" />
                {t('unblock')}
              </Button>
            )}
            <Button onClick={() => router.push(`/ru/schools/${school.id}/edit`)}>
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
              <CardDescription>Контактные данные школы</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {school.email && (
                <div className="flex items-center gap-3">
                  <Mail className="h-4 w-4 text-muted-foreground" />
                  <a
                    href={`mailto:${school.email}`}
                    className="text-primary hover:underline"
                  >
                    {school.email}
                  </a>
                </div>
              )}

              {school.phone && (
                <div className="flex items-center gap-3">
                  <Phone className="h-4 w-4 text-muted-foreground" />
                  <span>{school.phone}</span>
                </div>
              )}

              {school.address && (
                <div className="flex items-center gap-3">
                  <MapPin className="h-4 w-4 text-muted-foreground" />
                  <span>{school.address}</span>
                </div>
              )}

              {!school.email && !school.phone && !school.address && (
                <p className="text-sm text-muted-foreground">
                  Контактная информация не указана
                </p>
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
              <div className="flex items-center gap-3">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">Дата создания</p>
                  <p className="text-sm text-muted-foreground">
                    {format(new Date(school.created_at), 'dd MMMM yyyy, HH:mm', {
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
                    {format(new Date(school.updated_at), 'dd MMMM yyyy, HH:mm', {
                      locale: ru,
                    })}
                  </p>
                </div>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium">ID</p>
                <p className="text-sm text-muted-foreground">{school.id}</p>
              </div>
            </CardContent>
          </Card>

          {/* Description */}
          {school.description && (
            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle>Описание</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="whitespace-pre-wrap">{school.description}</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </RoleGuard>
  );
}
