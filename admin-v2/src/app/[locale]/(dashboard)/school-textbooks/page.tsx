'use client';

import { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import { BookOpen, Copy, Eye, Globe, School } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { RoleGuard } from '@/components/auth';
import { useSchoolTextbooks, useCustomizeTextbook, useDeleteSchoolTextbook } from '@/lib/hooks';
import type { Textbook } from '@/types';

export default function SchoolTextbooksPage() {
  const router = useRouter();
  const locale = 'ru';

  const { data: textbooks = [], isLoading } = useSchoolTextbooks(true);
  const customizeTextbook = useCustomizeTextbook();
  const deleteTextbook = useDeleteSchoolTextbook();

  const [customizeDialogOpen, setCustomizeDialogOpen] = useState(false);
  const [textbookToCustomize, setTextbookToCustomize] = useState<Textbook | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [textbookToDelete, setTextbookToDelete] = useState<Textbook | null>(null);

  // Split into global and school textbooks
  const globalTextbooks = useMemo(
    () => textbooks.filter((t) => t.school_id === null),
    [textbooks]
  );
  const schoolTextbooks = useMemo(
    () => textbooks.filter((t) => t.school_id !== null),
    [textbooks]
  );

  const handleCustomize = (textbook: Textbook) => {
    setTextbookToCustomize(textbook);
    setCustomizeDialogOpen(true);
  };

  const confirmCustomize = () => {
    if (textbookToCustomize) {
      customizeTextbook.mutate(textbookToCustomize.id, {
        onSuccess: () => {
          setCustomizeDialogOpen(false);
          setTextbookToCustomize(null);
        },
      });
    }
  };

  const handleDelete = (textbook: Textbook) => {
    setTextbookToDelete(textbook);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (textbookToDelete) {
      deleteTextbook.mutate(textbookToDelete.id);
    }
    setDeleteDialogOpen(false);
    setTextbookToDelete(null);
  };

  const TextbookCard = ({
    textbook,
    isGlobal,
  }: {
    textbook: Textbook;
    isGlobal: boolean;
  }) => {
    // Check if this global textbook was already customized
    const isAlreadyCustomized = isGlobal && schoolTextbooks.some(
      (t) => t.global_textbook_id === textbook.id
    );

    return (
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <CardTitle className="text-lg">{textbook.title}</CardTitle>
              <CardDescription>
                {textbook.subject} • {textbook.grade_level} класс
              </CardDescription>
            </div>
            <Badge variant={isGlobal ? 'secondary' : 'default'}>
              {isGlobal ? (
                <>
                  <Globe className="mr-1 h-3 w-3" />
                  Глобальный
                </>
              ) : (
                <>
                  <School className="mr-1 h-3 w-3" />
                  Школьный
                </>
              )}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {textbook.author && (
              <div className="text-sm">
                <span className="text-muted-foreground">Автор:</span>{' '}
                {textbook.author}
              </div>
            )}
            {textbook.year && (
              <div className="text-sm">
                <span className="text-muted-foreground">Год:</span> {textbook.year}
              </div>
            )}
            {textbook.is_customized && (
              <Badge variant="outline" className="text-xs">
                <Copy className="mr-1 h-3 w-3" />
                Кастомизированный
              </Badge>
            )}
            <div className="text-xs text-muted-foreground">
              Добавлен: {format(new Date(textbook.created_at), 'dd.MM.yyyy', { locale: ru })}
            </div>

            <div className="flex gap-2 pt-2">
              {isGlobal ? (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={() => router.push(`/${locale}/textbooks/${textbook.id}`)}
                  >
                    <Eye className="mr-2 h-4 w-4" />
                    Просмотр
                  </Button>
                  <Button
                    size="sm"
                    className="flex-1"
                    onClick={() => handleCustomize(textbook)}
                    disabled={isAlreadyCustomized || customizeTextbook.isPending}
                  >
                    <Copy className="mr-2 h-4 w-4" />
                    {isAlreadyCustomized ? 'Уже скопирован' : 'Кастомизировать'}
                  </Button>
                </>
              ) : (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={() => router.push(`/${locale}/school-textbooks/${textbook.id}`)}
                  >
                    <Eye className="mr-2 h-4 w-4" />
                    Просмотр
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleDelete(textbook)}
                  >
                    Удалить
                  </Button>
                </>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  if (isLoading) {
    return (
      <RoleGuard allowedRoles={['admin']}>
        <div className="space-y-6">
          <Skeleton className="h-10 w-64" />
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-48" />
            ))}
          </div>
        </div>
      </RoleGuard>
    );
  }

  return (
    <RoleGuard allowedRoles={['admin']}>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Библиотека учебников</h1>
          <p className="text-muted-foreground">
            Глобальные учебники доступны для просмотра. Кастомизируйте для редактирования.
          </p>
        </div>

        <Tabs defaultValue="global">
          <TabsList>
            <TabsTrigger value="global">
              <Globe className="mr-2 h-4 w-4" />
              Глобальные ({globalTextbooks.length})
            </TabsTrigger>
            <TabsTrigger value="school">
              <School className="mr-2 h-4 w-4" />
              Наши учебники ({schoolTextbooks.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="global" className="mt-6">
            {globalTextbooks.length > 0 ? (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {globalTextbooks.map((textbook) => (
                  <TextbookCard key={textbook.id} textbook={textbook} isGlobal />
                ))}
              </div>
            ) : (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <BookOpen className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">Нет глобальных учебников</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="school" className="mt-6">
            {schoolTextbooks.length > 0 ? (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {schoolTextbooks.map((textbook) => (
                  <TextbookCard key={textbook.id} textbook={textbook} isGlobal={false} />
                ))}
              </div>
            ) : (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <School className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground mb-4">
                    У вас пока нет школьных учебников
                  </p>
                  <p className="text-sm text-muted-foreground text-center max-w-md">
                    Перейдите во вкладку &quot;Глобальные&quot; и нажмите &quot;Кастомизировать&quot;
                    чтобы создать копию учебника для редактирования
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>

        <AlertDialog open={customizeDialogOpen} onOpenChange={setCustomizeDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Кастомизировать учебник?</AlertDialogTitle>
              <AlertDialogDescription>
                Будет создана копия учебника &quot;{textbookToCustomize?.title}&quot;
                со всеми главами и параграфами. Вы сможете редактировать копию.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Отмена</AlertDialogCancel>
              <AlertDialogAction
                onClick={confirmCustomize}
                disabled={customizeTextbook.isPending}
              >
                {customizeTextbook.isPending ? 'Копирование...' : 'Создать копию'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Удалить учебник?</AlertDialogTitle>
              <AlertDialogDescription>
                Вы уверены, что хотите удалить учебник &quot;{textbookToDelete?.title}&quot;?
                Все главы и параграфы будут удалены.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Отмена</AlertDialogCancel>
              <AlertDialogAction
                onClick={confirmDelete}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              >
                Удалить
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </RoleGuard>
  );
}
