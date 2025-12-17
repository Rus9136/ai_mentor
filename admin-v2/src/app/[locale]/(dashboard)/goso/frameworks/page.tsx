'use client';

import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import { Scale, BookOpen, Eye, Calendar, FileText } from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { RoleGuard } from '@/components/auth';
import { useFrameworks, useSubjects } from '@/lib/hooks/use-goso';

export default function FrameworksPage() {
  const t = useTranslations('nav');
  const router = useRouter();
  const locale = 'ru';

  const { data: frameworks = [], isLoading } = useFrameworks();
  const { data: subjects = [] } = useSubjects();

  const getSubjectName = (subjectId: number) => {
    const subject = subjects.find((s) => s.id === subjectId);
    return subject?.name_ru || 'Неизвестный предмет';
  };

  if (isLoading) {
    return (
      <RoleGuard allowedRoles={['super_admin']}>
        <div className="space-y-6">
          <Skeleton className="h-8 w-64" />
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <Skeleton className="h-48" />
            <Skeleton className="h-48" />
            <Skeleton className="h-48" />
          </div>
        </div>
      </RoleGuard>
    );
  }

  return (
    <RoleGuard allowedRoles={['super_admin']}>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{t('gosoFrameworks')}</h1>
          <p className="text-muted-foreground">
            Государственные общеобязательные стандарты образования
          </p>
        </div>

        {frameworks.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted mb-4">
                <Scale className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Нет стандартов</h3>
              <p className="text-muted-foreground text-center">
                ГОСО стандарты еще не загружены в систему
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {frameworks.map((framework) => (
              <Card key={framework.id} className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                      <Scale className="h-5 w-5 text-primary" />
                    </div>
                    <Badge variant={framework.is_active ? 'default' : 'secondary'}>
                      {framework.is_active ? 'Активен' : 'Неактивен'}
                    </Badge>
                  </div>
                  <CardTitle className="mt-4 text-lg">{framework.title_ru}</CardTitle>
                  <CardDescription>
                    <Badge variant="outline" className="mr-2">
                      <BookOpen className="mr-1 h-3 w-3" />
                      {getSubjectName(framework.subject_id)}
                    </Badge>
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {framework.description_ru && (
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {framework.description_ru}
                    </p>
                  )}

                  <div className="space-y-2 text-sm">
                    {framework.order_number && (
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <FileText className="h-4 w-4" />
                        <span>Приказ № {framework.order_number}</span>
                      </div>
                    )}
                    {framework.order_date && (
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <Calendar className="h-4 w-4" />
                        <span>
                          от {format(new Date(framework.order_date), 'dd MMMM yyyy', { locale: ru })}
                        </span>
                      </div>
                    )}
                  </div>

                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => router.push(`/${locale}/goso/frameworks/${framework.id}`)}
                  >
                    <Eye className="mr-2 h-4 w-4" />
                    Просмотреть
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </RoleGuard>
  );
}
