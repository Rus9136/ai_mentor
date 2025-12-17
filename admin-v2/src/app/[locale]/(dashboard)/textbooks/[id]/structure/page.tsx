'use client';

import { useParams, useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { ArrowLeft, BookOpen } from 'lucide-react';

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
import { RoleGuard } from '@/components/auth';
import { StructureEditor } from '@/components/textbooks';
import { useTextbook } from '@/lib/hooks/use-textbooks';

export default function TextbookStructurePage() {
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
          <div className="space-y-2">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-4 w-32" />
          </div>
        </div>
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
          </CardHeader>
          <CardContent className="space-y-4">
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
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
                  {t('structure')}
                </h1>
              </div>
              <div className="flex items-center gap-2 text-muted-foreground">
                <BookOpen className="h-4 w-4" />
                <span>{textbook.title}</span>
                <Badge variant="secondary">{textbook.grade_level} класс</Badge>
              </div>
            </div>
          </div>

          <Button
            variant="outline"
            onClick={() => router.push(`/ru/textbooks/${textbook.id}`)}
          >
            К учебнику
          </Button>
        </div>

        {/* Structure Editor */}
        <Card>
          <CardHeader>
            <CardTitle>Главы и параграфы</CardTitle>
            <CardDescription>
              Управляйте структурой учебника: добавляйте, редактируйте и удаляйте
              главы и параграфы
            </CardDescription>
          </CardHeader>
          <CardContent>
            <StructureEditor textbookId={textbookId} isSchool={false} />
          </CardContent>
        </Card>
      </div>
    </RoleGuard>
  );
}
