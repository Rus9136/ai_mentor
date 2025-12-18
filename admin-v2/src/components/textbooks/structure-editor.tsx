'use client';

import { useState } from 'react';
import {
  ChevronDown,
  ChevronRight,
  Plus,
  Pencil,
  Trash2,
  BookOpen,
  FileText,
  GripVertical,
  Layers,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
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
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  useChapters,
  useParagraphs,
  useParagraph,
  useCreateChapter,
  useUpdateChapter,
  useDeleteChapter,
  useCreateParagraph,
  useUpdateParagraph,
  useDeleteParagraph,
} from '@/lib/hooks/use-textbooks';
import type {
  ChapterCreateInput,
  ChapterUpdateInput,
  ParagraphCreateInput,
  ParagraphUpdateInput,
} from '@/lib/validations/textbook';
import type { Chapter, Paragraph } from '@/types';
import { ChapterDialog } from './chapter-dialog';
import { ParagraphDialog } from './paragraph-dialog';
import Link from 'next/link';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
  TooltipProvider,
} from '@/components/ui/tooltip';

interface StructureEditorProps {
  textbookId: number;
  isSchool?: boolean;
}

export function StructureEditor({ textbookId, isSchool = false }: StructureEditorProps) {
  const { data: chapters = [], isLoading: chaptersLoading } = useChapters(
    textbookId,
    isSchool
  );

  const createChapter = useCreateChapter(isSchool);
  const updateChapter = useUpdateChapter(isSchool);
  const deleteChapter = useDeleteChapter(isSchool);

  // Dialog states
  const [chapterDialogOpen, setChapterDialogOpen] = useState(false);
  const [selectedChapter, setSelectedChapter] = useState<Chapter | undefined>();
  const [deleteChapterDialogOpen, setDeleteChapterDialogOpen] = useState(false);
  const [chapterToDelete, setChapterToDelete] = useState<Chapter | null>(null);

  // Expanded chapters
  const [expandedChapters, setExpandedChapters] = useState<Set<number>>(new Set());

  const handleAddChapter = () => {
    setSelectedChapter(undefined);
    setChapterDialogOpen(true);
  };

  const handleEditChapter = (chapter: Chapter) => {
    setSelectedChapter(chapter);
    setChapterDialogOpen(true);
  };

  const handleDeleteChapter = (chapter: Chapter) => {
    setChapterToDelete(chapter);
    setDeleteChapterDialogOpen(true);
  };

  const confirmDeleteChapter = () => {
    if (chapterToDelete) {
      deleteChapter.mutate({
        id: chapterToDelete.id,
        textbookId,
      });
    }
    setDeleteChapterDialogOpen(false);
    setChapterToDelete(null);
  };

  const handleChapterSubmit = (data: ChapterCreateInput | ChapterUpdateInput) => {
    if (selectedChapter) {
      updateChapter.mutate(
        { id: selectedChapter.id, data: data as ChapterUpdateInput },
        { onSuccess: () => setChapterDialogOpen(false) }
      );
    } else {
      createChapter.mutate(data as ChapterCreateInput, {
        onSuccess: () => setChapterDialogOpen(false),
      });
    }
  };

  const toggleChapter = (chapterId: number) => {
    setExpandedChapters((prev) => {
      const next = new Set(prev);
      if (next.has(chapterId)) {
        next.delete(chapterId);
      } else {
        next.add(chapterId);
      }
      return next;
    });
  };

  const sortedChapters = [...chapters].sort((a, b) => a.order - b.order);

  if (chaptersLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-20 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BookOpen className="h-5 w-5 text-muted-foreground" />
          <span className="font-medium">
            {chapters.length} {chapters.length === 1 ? 'глава' : 'глав'}
          </span>
        </div>
        <Button onClick={handleAddChapter}>
          <Plus className="mr-2 h-4 w-4" />
          Добавить главу
        </Button>
      </div>

      {/* Empty state */}
      {chapters.length === 0 && (
        <Alert>
          <BookOpen className="h-4 w-4" />
          <AlertDescription>
            В учебнике пока нет глав. Нажмите &quot;Добавить главу&quot; для
            создания первой главы.
          </AlertDescription>
        </Alert>
      )}

      {/* Chapters list */}
      <div className="space-y-2">
        {sortedChapters.map((chapter) => (
          <ChapterItem
            key={chapter.id}
            chapter={chapter}
            isExpanded={expandedChapters.has(chapter.id)}
            onToggle={() => toggleChapter(chapter.id)}
            onEdit={() => handleEditChapter(chapter)}
            onDelete={() => handleDeleteChapter(chapter)}
            isSchool={isSchool}
          />
        ))}
      </div>

      {/* Chapter Dialog */}
      <ChapterDialog
        open={chapterDialogOpen}
        onOpenChange={setChapterDialogOpen}
        textbookId={textbookId}
        chapter={selectedChapter}
        nextNumber={chapters.length + 1}
        onSubmit={handleChapterSubmit}
        isLoading={createChapter.isPending || updateChapter.isPending}
      />

      {/* Delete Chapter Dialog */}
      <AlertDialog
        open={deleteChapterDialogOpen}
        onOpenChange={setDeleteChapterDialogOpen}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Удалить главу?</AlertDialogTitle>
            <AlertDialogDescription>
              Вы уверены, что хотите удалить главу &quot;{chapterToDelete?.title}
              &quot;? Все параграфы этой главы также будут удалены.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDeleteChapter}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Удалить
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

// Chapter Item Component
interface ChapterItemProps {
  chapter: Chapter;
  isExpanded: boolean;
  onToggle: () => void;
  onEdit: () => void;
  onDelete: () => void;
  isSchool: boolean;
}

function ChapterItem({
  chapter,
  isExpanded,
  onToggle,
  onEdit,
  onDelete,
  isSchool,
}: ChapterItemProps) {
  const { data: paragraphs = [], isLoading: paragraphsLoading } = useParagraphs(
    chapter.id,
    isSchool,
    isExpanded // Only fetch when expanded
  );

  const createParagraph = useCreateParagraph(isSchool);
  const updateParagraph = useUpdateParagraph(isSchool);
  const deleteParagraph = useDeleteParagraph(isSchool);

  const [paragraphDialogOpen, setParagraphDialogOpen] = useState(false);
  const [selectedParagraphId, setSelectedParagraphId] = useState<number | null>(null);
  const [deleteParagraphDialogOpen, setDeleteParagraphDialogOpen] = useState(false);
  const [paragraphToDelete, setParagraphToDelete] = useState<Paragraph | null>(null);

  // Fetch full paragraph data when editing (list doesn't include content)
  const { data: selectedParagraph, isLoading: paragraphLoading } = useParagraph(
    selectedParagraphId ?? 0,
    isSchool,
    selectedParagraphId !== null && paragraphDialogOpen
  );

  const handleAddParagraph = (e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedParagraphId(null);
    setParagraphDialogOpen(true);
  };

  const handleEditParagraph = (paragraph: Paragraph) => {
    setSelectedParagraphId(paragraph.id);
    setParagraphDialogOpen(true);
  };

  const handleDeleteParagraph = (paragraph: Paragraph) => {
    setParagraphToDelete(paragraph);
    setDeleteParagraphDialogOpen(true);
  };

  const confirmDeleteParagraph = () => {
    if (paragraphToDelete) {
      deleteParagraph.mutate({
        id: paragraphToDelete.id,
        chapterId: chapter.id,
      });
    }
    setDeleteParagraphDialogOpen(false);
    setParagraphToDelete(null);
  };

  const handleParagraphSubmit = (
    data: ParagraphCreateInput | ParagraphUpdateInput
  ) => {
    if (selectedParagraph) {
      updateParagraph.mutate(
        { id: selectedParagraph.id, data: data as ParagraphUpdateInput },
        { onSuccess: () => setParagraphDialogOpen(false) }
      );
    } else {
      createParagraph.mutate(data as ParagraphCreateInput, {
        onSuccess: () => setParagraphDialogOpen(false),
      });
    }
  };

  const sortedParagraphs = [...paragraphs].sort((a, b) => a.order - b.order);

  return (
    <>
      <Card>
        <Collapsible open={isExpanded} onOpenChange={onToggle}>
          <CollapsibleTrigger asChild>
            <CardContent className="p-4 cursor-pointer hover:bg-muted/50 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <GripVertical className="h-4 w-4 text-muted-foreground" />
                  {isExpanded ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                  <div>
                    <div className="font-medium">
                      Глава {chapter.number}: {chapter.title}
                    </div>
                    {chapter.description && (
                      <div className="text-sm text-muted-foreground line-clamp-1">
                        {chapter.description}
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {chapter.learning_objective && (
                    <Badge variant="outline" className="hidden sm:flex">
                      Цель обучения
                    </Badge>
                  )}
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={handleAddParagraph}
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => {
                      e.stopPropagation();
                      onEdit();
                    }}
                  >
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete();
                    }}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </CollapsibleTrigger>

          <CollapsibleContent>
            <div className="border-t px-4 py-3 bg-muted/30">
              {paragraphsLoading ? (
                <div className="space-y-2">
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                </div>
              ) : paragraphs.length === 0 ? (
                <div className="text-sm text-muted-foreground text-center py-4">
                  Нет параграфов в главе.{' '}
                  <button
                    className="text-primary hover:underline"
                    onClick={handleAddParagraph}
                  >
                    Добавить параграф
                  </button>
                </div>
              ) : (
                <TooltipProvider>
                  <div className="space-y-2">
                    {sortedParagraphs.map((paragraph) => (
                      <div
                        key={paragraph.id}
                        className="flex items-center justify-between p-3 rounded-md bg-background border"
                      >
                        <div className="flex items-center gap-3">
                          <FileText className="h-4 w-4 text-muted-foreground" />
                          <div>
                            <div className="font-medium">
                              §{paragraph.number}. {paragraph.title}
                            </div>
                            {paragraph.summary && (
                              <div className="text-sm text-muted-foreground line-clamp-1">
                                {paragraph.summary}
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-1">
                          {paragraph.questions && paragraph.questions.length > 0 && (
                            <Badge variant="outline" className="hidden sm:flex">
                              {paragraph.questions.length} вопр.
                            </Badge>
                          )}
                          {paragraph.key_terms && paragraph.key_terms.length > 0 && (
                            <Badge variant="secondary" className="hidden sm:flex">
                              {paragraph.key_terms.length} терминов
                            </Badge>
                          )}
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                asChild
                              >
                                <Link
                                  href={`/ru/textbooks/${chapter.textbook_id}/paragraphs/${paragraph.id}/content`}
                                >
                                  <Layers className="h-4 w-4" />
                                </Link>
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>Контент параграфа</p>
                            </TooltipContent>
                          </Tooltip>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleEditParagraph(paragraph)}
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDeleteParagraph(paragraph)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </TooltipProvider>
              )}
            </div>
          </CollapsibleContent>
        </Collapsible>
      </Card>

      {/* Paragraph Dialog */}
      <ParagraphDialog
        open={paragraphDialogOpen}
        onOpenChange={(open) => {
          setParagraphDialogOpen(open);
          if (!open) setSelectedParagraphId(null);
        }}
        chapterId={chapter.id}
        paragraph={selectedParagraph}
        nextNumber={paragraphs.length + 1}
        onSubmit={handleParagraphSubmit}
        isLoading={createParagraph.isPending || updateParagraph.isPending}
        isFetchingParagraph={paragraphLoading}
      />

      {/* Delete Paragraph Dialog */}
      <AlertDialog
        open={deleteParagraphDialogOpen}
        onOpenChange={setDeleteParagraphDialogOpen}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Удалить параграф?</AlertDialogTitle>
            <AlertDialogDescription>
              Вы уверены, что хотите удалить параграф &quot;
              {paragraphToDelete?.title}&quot;? Это действие нельзя отменить.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDeleteParagraph}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Удалить
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
