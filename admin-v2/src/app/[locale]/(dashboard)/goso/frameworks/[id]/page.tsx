'use client';

import { useParams, useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import {
  ArrowLeft,
  Scale,
  BookOpen,
  Calendar,
  FileText,
  ChevronRight,
  Target,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { RoleGuard } from '@/components/auth';
import { useFramework, useSections, useSubjects } from '@/lib/hooks/use-goso';

export default function FrameworkShowPage() {
  const params = useParams();
  const router = useRouter();
  const locale = 'ru';

  const frameworkId = Number(params.id);
  const { data: framework, isLoading: frameworkLoading } = useFramework(frameworkId);
  const { data: sections = [], isLoading: sectionsLoading } = useSections(frameworkId);
  const { data: subjects = [] } = useSubjects();

  const isLoading = frameworkLoading || sectionsLoading;

  const getSubjectName = (subjectId: number) => {
    const subject = subjects.find((s) => s.id === subjectId);
    return subject?.name_ru || 'Неизвестный предмет';
  };

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

  if (!framework) {
    return (
      <RoleGuard allowedRoles={['super_admin']}>
        <div className="text-center py-12">
          <p className="text-muted-foreground">Стандарт не найден</p>
          <Button
            variant="link"
            onClick={() => router.push(`/${locale}/goso/frameworks`)}
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
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push(`/${locale}/goso/frameworks`)}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h1 className="text-3xl font-bold tracking-tight">
                {framework.title_ru}
              </h1>
              <Badge variant={framework.is_active ? 'default' : 'secondary'}>
                {framework.is_active ? 'Активен' : 'Неактивен'}
              </Badge>
            </div>
            <p className="text-muted-foreground">
              {framework.code} • ГОСО Стандарт
            </p>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Scale className="h-5 w-5" />
                Информация о стандарте
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <div className="text-sm text-muted-foreground">Предмет</div>
                  <div className="font-medium flex items-center gap-2">
                    <BookOpen className="h-4 w-4" />
                    {getSubjectName(framework.subject_id)}
                  </div>
                </div>
                {framework.order_number && (
                  <div>
                    <div className="text-sm text-muted-foreground">Номер приказа</div>
                    <div className="font-medium flex items-center gap-2">
                      <FileText className="h-4 w-4" />
                      № {framework.order_number}
                    </div>
                  </div>
                )}
                {framework.order_date && (
                  <div>
                    <div className="text-sm text-muted-foreground">Дата приказа</div>
                    <div className="font-medium flex items-center gap-2">
                      <Calendar className="h-4 w-4" />
                      {format(new Date(framework.order_date), 'dd MMMM yyyy', { locale: ru })}
                    </div>
                  </div>
                )}
                {framework.ministry && (
                  <div>
                    <div className="text-sm text-muted-foreground">Министерство</div>
                    <div className="font-medium">{framework.ministry}</div>
                  </div>
                )}
              </div>

              {framework.description_ru && (
                <div>
                  <div className="text-sm text-muted-foreground mb-1">Описание</div>
                  <p>{framework.description_ru}</p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Статистика</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Разделов</span>
                <Badge variant="secondary">{sections.length}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Подразделов</span>
                <Badge variant="secondary">
                  {sections.reduce((acc, s) => acc + (s.subsections?.length || 0), 0)}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Целей обучения</span>
                <Badge variant="secondary">
                  {sections.reduce(
                    (acc, s) =>
                      acc +
                      (s.subsections?.reduce(
                        (a, sub) => a + (sub.outcomes?.length || 0),
                        0
                      ) || 0),
                    0
                  )}
                </Badge>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              Структура стандарта
            </CardTitle>
          </CardHeader>
          <CardContent>
            {sections.length === 0 ? (
              <p className="text-muted-foreground text-center py-8">
                Разделы не загружены
              </p>
            ) : (
              <div className="space-y-4">
                {sections
                  .sort((a, b) => a.display_order - b.display_order)
                  .map((section) => (
                    <Collapsible key={section.id} className="border rounded-lg">
                      <CollapsibleTrigger className="flex w-full items-center justify-between p-4 hover:bg-muted/50">
                        <div className="flex items-center gap-3">
                          <Badge variant="outline">{section.code}</Badge>
                          <span className="font-medium">{section.name_ru}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant="secondary">
                            {section.subsections?.length || 0} подразд.
                          </Badge>
                          <ChevronRight className="h-4 w-4 transition-transform duration-200 [[data-state=open]>div>&]:rotate-90" />
                        </div>
                      </CollapsibleTrigger>
                      <CollapsibleContent>
                        <div className="border-t px-4 py-2 space-y-2">
                          {section.subsections
                            ?.sort((a, b) => a.display_order - b.display_order)
                            .map((subsection) => (
                              <div
                                key={subsection.id}
                                className="ml-4 p-3 rounded-md bg-muted/30"
                              >
                                <div className="flex items-center gap-2 mb-2">
                                  <Badge variant="outline" className="text-xs">
                                    {subsection.code}
                                  </Badge>
                                  <span className="text-sm font-medium">
                                    {subsection.name_ru}
                                  </span>
                                  <Badge variant="secondary" className="text-xs ml-auto">
                                    {subsection.outcomes?.length || 0} целей
                                  </Badge>
                                </div>
                                {subsection.outcomes && subsection.outcomes.length > 0 && (
                                  <div className="ml-4 mt-2 space-y-1">
                                    {subsection.outcomes
                                      .sort((a, b) => a.display_order - b.display_order)
                                      .slice(0, 5)
                                      .map((outcome) => (
                                        <div
                                          key={outcome.id}
                                          className="text-xs text-muted-foreground flex items-start gap-2"
                                        >
                                          <Badge
                                            variant="outline"
                                            className="shrink-0 text-[10px]"
                                          >
                                            {outcome.grade} кл.
                                          </Badge>
                                          <span className="line-clamp-1">
                                            {outcome.title_ru}
                                          </span>
                                        </div>
                                      ))}
                                    {(subsection.outcomes?.length || 0) > 5 && (
                                      <Button
                                        variant="link"
                                        size="sm"
                                        className="text-xs p-0 h-auto"
                                        onClick={() =>
                                          router.push(
                                            `/${locale}/goso/outcomes?subsection_id=${subsection.id}`
                                          )
                                        }
                                      >
                                        ... еще {(subsection.outcomes?.length || 0) - 5} целей
                                      </Button>
                                    )}
                                  </div>
                                )}
                              </div>
                            ))}
                        </div>
                      </CollapsibleContent>
                    </Collapsible>
                  ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </RoleGuard>
  );
}
