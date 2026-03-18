'use client';

import { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import {
  Plus,
  FileQuestion,
  Eye,
  Edit,
  Trash2,
  ChevronRight,
  ChevronDown,
  BookOpen,
  FolderOpen,
  FileText,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useTeacherTests, useDeleteTeacherTest } from '@/lib/hooks/use-teacher-tests';
import type { Test, DifficultyLevel, TestPurpose } from '@/types/test';

const difficultyLabels: Record<DifficultyLevel, string> = {
  easy: 'Легкий',
  medium: 'Средний',
  hard: 'Сложный',
};

const difficultyVariants: Record<DifficultyLevel, 'default' | 'secondary' | 'destructive'> = {
  easy: 'default',
  medium: 'secondary',
  hard: 'destructive',
};

const purposeLabels: Record<TestPurpose, string> = {
  diagnostic: 'Диагностический',
  formative: 'Формативный',
  summative: 'Суммативный',
  practice: 'Практический',
};

interface TextbookNode {
  textbook_id: number;
  textbook_title: string;
  grade_level: number | null;
  chapters: ChapterNode[];
  tests: Test[];
}

interface ChapterNode {
  chapter_id: number;
  chapter_title: string;
  paragraphs: ParagraphNode[];
  tests: Test[];
}

interface ParagraphNode {
  paragraph_id: number;
  paragraph_title: string;
  tests: Test[];
}

function buildTree(tests: Test[]): TextbookNode[] {
  const textbookMap = new Map<number, TextbookNode>();

  for (const test of tests) {
    const tbId = test.textbook_id;
    if (!tbId) continue;

    if (!textbookMap.has(tbId)) {
      textbookMap.set(tbId, {
        textbook_id: tbId,
        textbook_title: test.textbook_title || `Учебник #${tbId}`,
        grade_level: test.grade_level ?? null,
        chapters: [],
        tests: [],
      });
    }
    const tbNode = textbookMap.get(tbId)!;

    const chId = test.chapter_id;
    if (!chId) {
      tbNode.tests.push(test);
      continue;
    }

    let chNode = tbNode.chapters.find((c) => c.chapter_id === chId);
    if (!chNode) {
      chNode = {
        chapter_id: chId,
        chapter_title: test.chapter_title || `Глава #${chId}`,
        paragraphs: [],
        tests: [],
      };
      tbNode.chapters.push(chNode);
    }

    const pId = test.paragraph_id;
    if (!pId) {
      chNode.tests.push(test);
      continue;
    }

    let pNode = chNode.paragraphs.find((p) => p.paragraph_id === pId);
    if (!pNode) {
      pNode = {
        paragraph_id: pId,
        paragraph_title: test.paragraph_title || `Параграф #${pId}`,
        tests: [],
      };
      chNode.paragraphs.push(pNode);
    }

    pNode.tests.push(test);
  }

  const nodes = Array.from(textbookMap.values());
  nodes.sort((a, b) => (a.grade_level ?? 0) - (b.grade_level ?? 0));
  return nodes;
}

function countTests(node: TextbookNode | ChapterNode): number {
  if ('chapters' in node) {
    return (
      node.tests.length +
      node.chapters.reduce(
        (sum, ch) => sum + ch.tests.length + ch.paragraphs.reduce((s, p) => s + p.tests.length, 0),
        0
      )
    );
  }
  return node.tests.length + node.paragraphs.reduce((s, p) => s + p.tests.length, 0);
}

export default function TeacherTestsPage() {
  const router = useRouter();
  const t = useTranslations('common');
  const locale = 'ru';

  const [gradeFilter, setGradeFilter] = useState<string>('all');
  const [search, setSearch] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [testToDelete, setTestToDelete] = useState<Test | null>(null);
  const [expandedTextbooks, setExpandedTextbooks] = useState<Set<number>>(new Set());
  const [expandedChapters, setExpandedChapters] = useState<Set<number>>(new Set());
  const [expandedParagraphs, setExpandedParagraphs] = useState<Set<number>>(new Set());

  const { data, isLoading } = useTeacherTests({
    include_global: true,
    page_size: 500,
  });
  const deleteTest = useDeleteTeacherTest();

  const allTests = data?.items ?? [];

  // Available grades from all tests
  const availableGrades = useMemo(() => {
    const grades = new Set<number>();
    for (const test of allTests) {
      if (test.grade_level) grades.add(test.grade_level);
    }
    return Array.from(grades).sort((a, b) => a - b);
  }, [allTests]);

  // Apply grade + search filters on frontend
  const filtered = useMemo(() => {
    let result = allTests;
    if (gradeFilter !== 'all') {
      const grade = parseInt(gradeFilter);
      result = result.filter((t) => t.grade_level === grade);
    }
    if (search) {
      const q = search.toLowerCase();
      result = result.filter(
        (test) =>
          test.title.toLowerCase().includes(q) ||
          (test.textbook_title && test.textbook_title.toLowerCase().includes(q)) ||
          (test.chapter_title && test.chapter_title.toLowerCase().includes(q)) ||
          (test.paragraph_title && test.paragraph_title.toLowerCase().includes(q))
      );
    }
    return result;
  }, [allTests, gradeFilter, search]);

  const tree = useMemo(() => buildTree(filtered), [filtered]);

  const toggleTextbook = (id: number) => {
    setExpandedTextbooks((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleChapter = (id: number) => {
    setExpandedChapters((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleParagraph = (id: number) => {
    setExpandedParagraphs((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const expandAll = () => {
    setExpandedTextbooks(new Set(tree.map((t) => t.textbook_id)));
    setExpandedChapters(new Set(tree.flatMap((t) => t.chapters.map((c) => c.chapter_id))));
    setExpandedParagraphs(
      new Set(tree.flatMap((t) => t.chapters.flatMap((c) => c.paragraphs.map((p) => p.paragraph_id))))
    );
  };

  const collapseAll = () => {
    setExpandedTextbooks(new Set());
    setExpandedChapters(new Set());
    setExpandedParagraphs(new Set());
  };

  const handleDelete = (test: Test) => {
    setTestToDelete(test);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (testToDelete) {
      deleteTest.mutate(testToDelete.id);
    }
    setDeleteDialogOpen(false);
    setTestToDelete(null);
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-10 w-64 bg-muted animate-pulse rounded" />
        <div className="h-[400px] w-full bg-muted animate-pulse rounded" />
      </div>
    );
  }

  const renderTestRow = (test: Test, indent: number) => (
    <div
      key={test.id}
      className="flex items-center gap-2 py-2 px-3 hover:bg-muted/50 rounded-md group"
      style={{ paddingLeft: `${indent * 24 + 12}px` }}
    >
      <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
      <div className="flex-1 min-w-0">
        <span className="text-sm font-medium truncate block">{test.title}</span>
      </div>
      <Badge variant="outline" className="shrink-0 text-xs">
        {purposeLabels[test.test_purpose]}
      </Badge>
      <Badge variant={difficultyVariants[test.difficulty]} className="shrink-0 text-xs">
        {difficultyLabels[test.difficulty]}
      </Badge>
      <span className="text-xs text-muted-foreground shrink-0 w-10 text-right">
        {test.passing_score}%
      </span>
      <div className="flex gap-0.5 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={() => router.push(`/${locale}/tests/${test.id}`)}
        >
          <Eye className="h-3.5 w-3.5" />
        </Button>
        {test.school_id !== null && (
          <>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => router.push(`/${locale}/tests/${test.id}/edit`)}
            >
              <Edit className="h-3.5 w-3.5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => handleDelete(test)}
            >
              <Trash2 className="h-3.5 w-3.5" />
            </Button>
          </>
        )}
      </div>
    </div>
  );

  const renderParagraphNode = (pNode: ParagraphNode, indent: number) => {
    const isExpanded = expandedParagraphs.has(pNode.paragraph_id);
    return (
      <div key={`p-${pNode.paragraph_id}`}>
        <button
          onClick={() => toggleParagraph(pNode.paragraph_id)}
          className="flex items-center gap-2 w-full py-1.5 px-3 hover:bg-muted/50 rounded-md text-left"
          style={{ paddingLeft: `${indent * 24 + 12}px` }}
        >
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
          ) : (
            <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
          )}
          <FileText className="h-4 w-4 text-blue-500 shrink-0" />
          <span className="text-sm truncate">{pNode.paragraph_title}</span>
          <Badge variant="secondary" className="ml-auto text-xs shrink-0">
            {pNode.tests.length}
          </Badge>
        </button>
        {isExpanded && pNode.tests.map((test) => renderTestRow(test, indent + 1))}
      </div>
    );
  };

  const renderChapterNode = (chNode: ChapterNode, indent: number) => {
    const isExpanded = expandedChapters.has(chNode.chapter_id);
    const totalTests = countTests(chNode);
    return (
      <div key={`ch-${chNode.chapter_id}`}>
        <button
          onClick={() => toggleChapter(chNode.chapter_id)}
          className="flex items-center gap-2 w-full py-2 px-3 hover:bg-muted/50 rounded-md text-left"
          style={{ paddingLeft: `${indent * 24 + 12}px` }}
        >
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
          ) : (
            <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
          )}
          <FolderOpen className="h-4 w-4 text-amber-500 shrink-0" />
          <span className="text-sm font-medium truncate">{chNode.chapter_title}</span>
          <Badge variant="secondary" className="ml-auto text-xs shrink-0">
            {totalTests}
          </Badge>
        </button>
        {isExpanded && (
          <>
            {chNode.tests.map((test) => renderTestRow(test, indent + 1))}
            {chNode.paragraphs.map((pNode) => renderParagraphNode(pNode, indent + 1))}
          </>
        )}
      </div>
    );
  };

  const renderTextbookNode = (tbNode: TextbookNode) => {
    const isExpanded = expandedTextbooks.has(tbNode.textbook_id);
    const totalTests = countTests(tbNode);
    return (
      <div key={`tb-${tbNode.textbook_id}`} className="border rounded-lg overflow-hidden">
        <button
          onClick={() => toggleTextbook(tbNode.textbook_id)}
          className="flex items-center gap-3 w-full py-3 px-4 hover:bg-muted/50 text-left bg-muted/30"
        >
          {isExpanded ? (
            <ChevronDown className="h-5 w-5 text-muted-foreground shrink-0" />
          ) : (
            <ChevronRight className="h-5 w-5 text-muted-foreground shrink-0" />
          )}
          <BookOpen className="h-5 w-5 text-primary shrink-0" />
          <div className="flex-1 min-w-0">
            <span className="font-semibold text-sm truncate block">{tbNode.textbook_title}</span>
            {tbNode.grade_level && (
              <span className="text-xs text-muted-foreground">{tbNode.grade_level} класс</span>
            )}
          </div>
          <Badge variant="outline" className="shrink-0">
            {totalTests} {totalTests === 1 ? 'тест' : totalTests < 5 ? 'теста' : 'тестов'}
          </Badge>
        </button>
        {isExpanded && (
          <div className="py-1">
            {tbNode.tests.map((test) => renderTestRow(test, 1))}
            {tbNode.chapters.map((chNode) => renderChapterNode(chNode, 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Тесты</h1>
          <p className="text-muted-foreground">
            Тесты по вашему предмету ({filtered.length} шт.)
          </p>
        </div>
        <Button onClick={() => router.push(`/${locale}/tests/create`)}>
          <Plus className="mr-2 h-4 w-4" />
          Создать тест
        </Button>
      </div>

      {allTests.length > 0 ? (
        <>
          <div className="flex items-center gap-3 flex-wrap">
            <Input
              placeholder="Поиск по названию..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="max-w-sm"
            />
            <Select value={gradeFilter} onValueChange={setGradeFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Все классы" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Все классы</SelectItem>
                {availableGrades.map((g) => (
                  <SelectItem key={g} value={String(g)}>
                    {g} класс
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <div className="flex gap-1 ml-auto">
              <Button variant="outline" size="sm" onClick={expandAll}>
                Развернуть все
              </Button>
              <Button variant="outline" size="sm" onClick={collapseAll}>
                Свернуть все
              </Button>
            </div>
          </div>

          {tree.length > 0 ? (
            <div className="space-y-3">
              {tree.map((tbNode) => renderTextbookNode(tbNode))}
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <FileQuestion className="h-12 w-12 text-muted-foreground mb-4" />
                <p className="text-muted-foreground">Ничего не найдено</p>
              </CardContent>
            </Card>
          )}
        </>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <FileQuestion className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground mb-4">У вас пока нет тестов</p>
            <Button onClick={() => router.push(`/${locale}/tests/create`)}>
              <Plus className="mr-2 h-4 w-4" />
              Создать первый тест
            </Button>
          </CardContent>
        </Card>
      )}

      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Удалить тест?</DialogTitle>
            <DialogDescription>
              Вы уверены, что хотите удалить тест &quot;{testToDelete?.title}&quot;?
              Все вопросы будут удалены.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              Отмена
            </Button>
            <Button variant="destructive" onClick={confirmDelete}>
              Удалить
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
