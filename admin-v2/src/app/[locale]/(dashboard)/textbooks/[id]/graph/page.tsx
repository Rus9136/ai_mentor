'use client';

import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, BookOpen, GitBranch } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { RoleGuard } from '@/components/auth';
import { PrerequisiteGraph } from '@/components/textbooks/prerequisite-graph';
import { useTextbook } from '@/lib/hooks/use-textbooks';
import { useTextbookPrerequisiteGraph } from '@/lib/hooks/use-prerequisites';

export default function TextbookGraphPage() {
  const params = useParams();
  const router = useRouter();
  const textbookId = Number(params.id);

  const { data: textbook, isLoading: textbookLoading } = useTextbook(textbookId, false);
  const { data: graph, isLoading: graphLoading } = useTextbookPrerequisiteGraph(textbookId);

  const isLoading = textbookLoading || graphLoading;

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
        <Skeleton className="h-[600px] w-full rounded-lg" />
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

  const hasEdges = graph && graph.total_edges > 0;
  const hasNodes = graph && graph.nodes.length > 0;

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
                  Граф зависимостей
                </h1>
                {graph && (
                  <Badge variant="secondary">
                    {graph.total_edges} связей
                  </Badge>
                )}
              </div>
              <div className="flex items-center gap-2 text-muted-foreground">
                <BookOpen className="h-4 w-4" />
                <span>{textbook.title}</span>
                <Badge variant="secondary">{textbook.grade_level} класс</Badge>
              </div>
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => router.push(`/ru/textbooks/${textbook.id}/structure`)}
            >
              <BookOpen className="mr-2 h-4 w-4" />
              Структура
            </Button>
            <Button
              variant="outline"
              onClick={() => router.push(`/ru/textbooks/${textbook.id}`)}
            >
              К учебнику
            </Button>
          </div>
        </div>

        {/* Graph */}
        {!hasNodes ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-16">
              <GitBranch className="h-12 w-12 text-muted-foreground/30 mb-4" />
              <p className="text-lg font-medium text-muted-foreground">
                Нет параграфов
              </p>
              <p className="text-sm text-muted-foreground/70 mt-1">
                Добавьте параграфы в учебник через раздел &quot;Структура&quot;
              </p>
            </CardContent>
          </Card>
        ) : !hasEdges ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-16">
              <GitBranch className="h-12 w-12 text-muted-foreground/30 mb-4" />
              <p className="text-lg font-medium text-muted-foreground">
                Нет связей между параграфами
              </p>
              <p className="text-sm text-muted-foreground/70 mt-1">
                Добавьте пререквизиты в параграфах через раздел &quot;Структура&quot;
              </p>
            </CardContent>
          </Card>
        ) : (
          <Card className="overflow-hidden">
            <CardHeader className="py-3">
              <CardTitle className="text-base flex items-center gap-2">
                <GitBranch className="h-4 w-4" />
                Траектория обучения
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0 h-[700px]">
              <PrerequisiteGraph
                graphNodes={graph.nodes}
                graphEdges={graph.edges}
              />
            </CardContent>
          </Card>
        )}
      </div>
    </RoleGuard>
  );
}
