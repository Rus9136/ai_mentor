'use client';

import { useRouter } from 'next/navigation';
import { Building2 } from 'lucide-react';

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { RoleGuard } from '@/components/auth';
import { SettingsForm } from '@/components/forms';
import { useSchoolSettings, useUpdateSchoolSettings } from '@/lib/hooks';
import type { SettingsUpdateInput } from '@/lib/validations/settings';

export default function SettingsPage() {
  const { data: school, isLoading } = useSchoolSettings();
  const updateSettings = useUpdateSchoolSettings();

  const handleSubmit = (data: SettingsUpdateInput) => {
    updateSettings.mutate(data);
  };

  if (isLoading) {
    return (
      <RoleGuard allowedRoles={['admin']}>
        <div className="space-y-6">
          <Skeleton className="h-10 w-64" />
          <Card>
            <CardHeader>
              <Skeleton className="h-6 w-48" />
            </CardHeader>
            <CardContent className="space-y-4">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-20 w-full" />
            </CardContent>
          </Card>
        </div>
      </RoleGuard>
    );
  }

  if (!school) {
    return (
      <RoleGuard allowedRoles={['admin']}>
        <div className="flex flex-col items-center justify-center py-12">
          <p className="text-muted-foreground">Не удалось загрузить настройки</p>
        </div>
      </RoleGuard>
    );
  }

  return (
    <RoleGuard allowedRoles={['admin']}>
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
            <Building2 className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Настройки школы</h1>
            <div className="flex items-center gap-2 mt-1">
              <code className="text-sm text-muted-foreground">{school.code}</code>
              <Badge variant={school.is_active ? 'default' : 'secondary'}>
                {school.is_active ? 'Активна' : 'Неактивна'}
              </Badge>
            </div>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle>Общая информация</CardTitle>
              <CardDescription>
                Основные данные о вашей школе
              </CardDescription>
            </CardHeader>
            <CardContent>
              <SettingsForm
                school={school}
                onSubmit={handleSubmit}
                isLoading={updateSettings.isPending}
              />
            </CardContent>
          </Card>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Статистика</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">ID школы</span>
                  <span className="font-mono">{school.id}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Код</span>
                  <code className="rounded bg-muted px-2 py-1 text-sm">
                    {school.code}
                  </code>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Контакты</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {school.email ? (
                  <div>
                    <div className="text-xs text-muted-foreground">Email</div>
                    <a
                      href={`mailto:${school.email}`}
                      className="text-sm text-primary hover:underline"
                    >
                      {school.email}
                    </a>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">Email не указан</p>
                )}
                {school.phone ? (
                  <div>
                    <div className="text-xs text-muted-foreground">Телефон</div>
                    <a
                      href={`tel:${school.phone}`}
                      className="text-sm text-primary hover:underline"
                    >
                      {school.phone}
                    </a>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">Телефон не указан</p>
                )}
                {school.address && (
                  <div>
                    <div className="text-xs text-muted-foreground">Адрес</div>
                    <p className="text-sm">{school.address}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </RoleGuard>
  );
}
