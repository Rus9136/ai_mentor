'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, BookOpen, GitBranch, Network, List } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { RoleGuard } from '@/components/auth';
import { PrerequisiteGraph } from '@/components/textbooks/prerequisite-graph';
import { PrerequisiteTable } from '@/components/textbooks/prerequisite-table';
import { useTextbook } from '@/lib/hooks/use-textbooks';
import { useTextbookPrerequisiteGraph } from '@/lib/hooks/use-prerequisites';

type ViewMode = 'graph' | 'table';

export default function TextbookGraphPage() {
  const params = useParams();
  const router = useRouter();
  const textbookId = Number(params.id);
  const [viewMode, setViewMode] = useState<ViewMode>('table');

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
              <div className="flex items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  <GitBranch className="h-4 w-4" />
                  Траектория обучения
                </CardTitle>
                {/* View mode toggle */}
                <div className="flex items-center rounded-lg border bg-muted/30 p-0.5">
                  <button
                    onClick={() => setViewMode('table')}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                      viewMode === 'table'
                        ? 'bg-background shadow-sm text-foreground'
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    <List className="h-3.5 w-3.5" />
                    Таблица
                  </button>
                  <button
                    onClick={() => setViewMode('graph')}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                      viewMode === 'graph'
                        ? 'bg-background shadow-sm text-foreground'
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    <Network className="h-3.5 w-3.5" />
                    Граф
                  </button>
                </div>
              </div>
            </CardHeader>
            <CardContent className={`p-0 ${viewMode === 'graph' ? 'h-[700px]' : ''}`}>
              {viewMode === 'graph' ? (
                <PrerequisiteGraph
                  graphNodes={graph.nodes}
                  graphEdges={graph.edges}
                />
              ) : (
                <PrerequisiteTable
                  graphNodes={graph.nodes}
                  graphEdges={graph.edges}
                  currentTextbookId={textbookId}
                />
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </RoleGuard>
  );
}
