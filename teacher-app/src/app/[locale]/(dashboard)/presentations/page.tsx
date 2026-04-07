'use client';

import { Link } from '@/i18n/routing';
import { Plus, Presentation, Trash2, Download, Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { usePresentations, useDeletePresentation } from '@/lib/hooks/use-presentations';
import { exportPresentationPptx } from '@/lib/api/presentations';

export default function PresentationsListPage() {
  const { data: presentations, isLoading } = usePresentations();
  const deleteMutation = useDeletePresentation();

  const handleDelete = (id: number) => {
    if (!confirm('Удалить эту презентацию?')) return;
    deleteMutation.mutate(id);
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Мои презентации</h1>
          <p className="text-sm text-muted-foreground">Сохранённые AI-презентации</p>
        </div>
        <Link href="/presentations/create">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Новая презентация
          </Button>
        </Link>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <Presentation className="h-5 w-5" />
            Презентации
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-8">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            </div>
          ) : !presentations?.length ? (
            <div className="py-8 text-center text-muted-foreground">
              Презентаций пока нет
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Тема</TableHead>
                  <TableHead>Предмет</TableHead>
                  <TableHead>Язык</TableHead>
                  <TableHead>Слайдов</TableHead>
                  <TableHead>Дата</TableHead>
                  <TableHead className="text-right">Действия</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {presentations.map((pres) => (
                  <TableRow key={pres.id}>
                    <TableCell className="max-w-[300px] truncate font-medium">
                      {pres.title}
                    </TableCell>
                    <TableCell>
                      {pres.subject} {pres.grade_level && `${pres.grade_level}-сынып`}
                    </TableCell>
                    <TableCell>{pres.language === 'kk' ? 'QAZ' : 'RUS'}</TableCell>
                    <TableCell>{pres.slide_count}</TableCell>
                    <TableCell>{formatDate(pres.created_at)}</TableCell>
                    <TableCell>
                      <div className="flex justify-end gap-1">
                        <Link href={`/presentations/${pres.id}`}>
                          <Button variant="ghost" size="icon">
                            <Eye className="h-4 w-4" />
                          </Button>
                        </Link>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => exportPresentationPptx(pres.id)}
                        >
                          <Download className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(pres.id)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
