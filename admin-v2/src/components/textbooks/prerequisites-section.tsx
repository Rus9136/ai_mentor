'use client';

import { useState, useMemo } from 'react';
import { Plus, Trash2, Loader2, GitBranch, ArrowRight } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
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
import {
  usePrerequisites,
  useCreatePrerequisite,
  useDeletePrerequisite,
} from '@/lib/hooks/use-prerequisites';
import { useTextbooks } from '@/lib/hooks/use-textbooks';
import type { Paragraph, Textbook } from '@/types';
import type { PrerequisiteResponse } from '@/lib/api/prerequisites';

interface PrerequisitesSectionProps {
  paragraphId: number;
  textbookId: number;
  subjectId?: number | null;
}

interface ParagraphEntry {
  paragraph: Paragraph;
  chapterTitle: string;
  textbookTitle: string;
  gradeLevel: number;
  textbookId: number;
}

const STRENGTH_LABELS: Record<string, string> = {
  required: 'Обязательный',
  recommended: 'Рекомендуемый',
};

const STRENGTH_VARIANTS: Record<string, 'default' | 'secondary' | 'outline'> = {
  required: 'default',
  recommended: 'secondary',
};

export function PrerequisitesSection({
  paragraphId,
  textbookId,
  subjectId,
}: PrerequisitesSectionProps) {
  const { data: prerequisites = [], isLoading } = usePrerequisites(paragraphId);
  const createMutation = useCreatePrerequisite();
  const deleteMutation = useDeletePrerequisite();

  // Load all global textbooks (to filter by subject)
  const { data: allTextbooks = [] } = useTextbooks(false);

  const [pickerOpen, setPickerOpen] = useState(false);
  const [strength, setStrength] = useState<string>('required');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [prereqToDelete, setPrereqToDelete] = useState<PrerequisiteResponse | null>(null);

  const [allParagraphs, setAllParagraphs] = useState<ParagraphEntry[]>([]);
  const [paragraphsLoaded, setParagraphsLoaded] = useState(false);

  // Get textbooks of the same subject (or just current textbook if no subjectId)
  const subjectTextbooks = useMemo(() => {
    if (!subjectId) {
      return allTextbooks.filter((t) => t.id === textbookId);
    }
    return allTextbooks
      .filter((t) => t.subject_id === subjectId)
      .sort((a, b) => (a.grade_level || 0) - (b.grade_level || 0));
  }, [allTextbooks, subjectId, textbookId]);

  // Load paragraphs from all textbooks of the subject when picker opens
  const loadAllParagraphs = async () => {
    if (paragraphsLoaded || subjectTextbooks.length === 0) return;

    const { textbooksApi } = await import('@/lib/api/textbooks');
    const allParas: ParagraphEntry[] = [];

    for (const tb of subjectTextbooks) {
      try {
        const chapters = await textbooksApi.getChapters(tb.id, false);
        for (const chapter of chapters) {
          try {
            const paragraphs = await textbooksApi.getParagraphs(chapter.id, false);
            for (const p of paragraphs) {
              allParas.push({
                paragraph: p,
                chapterTitle: chapter.title || `Глава ${chapter.number}`,
                textbookTitle: tb.title,
                gradeLevel: tb.grade_level || 0,
                textbookId: tb.id,
              });
            }
          } catch {
            // Skip chapters with errors
          }
        }
      } catch {
        // Skip textbooks with errors
      }
    }

    setAllParagraphs(allParas);
    setParagraphsLoaded(true);
  };

  // Filter out current paragraph and already-added prerequisites from picker
  const existingPrereqIds = useMemo(
    () => new Set(prerequisites.map((p) => p.prerequisite_paragraph_id)),
    [prerequisites]
  );

  const availableParagraphs = useMemo(
    () =>
      allParagraphs.filter(
        ({ paragraph }) =>
          paragraph.id !== paragraphId && !existingPrereqIds.has(paragraph.id)
      ),
    [allParagraphs, paragraphId, existingPrereqIds]
  );

  // Group available paragraphs by textbook for the picker
  const groupedByTextbook = useMemo(() => {
    const groups: Record<number, { textbook: { title: string; gradeLevel: number }; items: ParagraphEntry[] }> = {};
    for (const entry of availableParagraphs) {
      if (!groups[entry.textbookId]) {
        groups[entry.textbookId] = {
          textbook: { title: entry.textbookTitle, gradeLevel: entry.gradeLevel },
          items: [],
        };
      }
      groups[entry.textbookId].items.push(entry);
    }
    return groups;
  }, [availableParagraphs]);

  const hasMultipleTextbooks = Object.keys(groupedByTextbook).length > 1;

  const handleAdd = (prereqParagraphId: number) => {
    createMutation.mutate(
      {
        paragraphId,
        data: {
          prerequisite_paragraph_id: prereqParagraphId,
          strength,
        },
      },
      {
        onSuccess: () => setPickerOpen(false),
      }
    );
  };

  const handleDelete = (prereq: PrerequisiteResponse) => {
    setPrereqToDelete(prereq);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (prereqToDelete) {
      deleteMutation.mutate({
        id: prereqToDelete.id,
        paragraphId,
      });
    }
    setDeleteDialogOpen(false);
    setPrereqToDelete(null);
  };

  // Check if a prerequisite is from a different textbook
  const isCrossTextbook = (prereq: PrerequisiteResponse) => {
    return prereq.prerequisite_textbook_title && prereq.prerequisite_grade_level != null;
  };

  return (
    <>
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <GitBranch className="h-4 w-4" />
              Пререквизиты (зависимости)
            </CardTitle>
            <div className="flex items-center gap-2">
              <Select value={strength} onValueChange={setStrength}>
                <SelectTrigger className="w-[150px] h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="required">Обязательный</SelectItem>
                  <SelectItem value="recommended">Рекомендуемый</SelectItem>
                </SelectContent>
              </Select>
              <Popover
                open={pickerOpen}
                onOpenChange={(open) => {
                  setPickerOpen(open);
                  if (open) loadAllParagraphs();
                }}
              >
                <PopoverTrigger asChild>
                  <Button type="button" variant="outline" size="sm">
                    <Plus className="h-4 w-4 mr-1" />
                    Добавить
                  </Button>
                </PopoverTrigger>
                <PopoverContent
                  className="w-[500px] p-0"
                  align="end"
                  side="bottom"
                  sideOffset={4}
                  onOpenAutoFocus={(e) => e.preventDefault()}
                >
                  <Command>
                    <CommandInput placeholder="Поиск параграфа..." />
                    <CommandList style={{ maxHeight: '350px', overflowY: 'auto' }}>
                      {!paragraphsLoaded ? (
                        <div className="flex items-center justify-center py-6">
                          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                        </div>
                      ) : availableParagraphs.length === 0 ? (
                        <CommandEmpty>Нет доступных параграфов</CommandEmpty>
                      ) : (
                        Object.entries(groupedByTextbook).map(([tbId, group]) => (
                          <CommandGroup
                            key={tbId}
                            heading={
                              hasMultipleTextbooks
                                ? `${group.textbook.title} (${group.textbook.gradeLevel} класс)`
                                : undefined
                            }
                          >
                            {group.items.map(({ paragraph: p, chapterTitle }) => (
                              <CommandItem
                                key={p.id}
                                value={`§${p.number} ${p.title} ${chapterTitle} ${group.textbook.title}`}
                                onSelect={() => handleAdd(p.id)}
                                disabled={createMutation.isPending}
                              >
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-1.5">
                                    <Badge variant="outline" className="text-xs shrink-0">
                                      §{p.number}
                                    </Badge>
                                    <span className="text-xs text-muted-foreground truncate">
                                      {chapterTitle}
                                    </span>
                                  </div>
                                  <p className="text-sm mt-0.5 truncate">{p.title}</p>
                                </div>
                              </CommandItem>
                            ))}
                          </CommandGroup>
                        ))
                      )}
                    </CommandList>
                  </Command>
                </PopoverContent>
              </Popover>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-2">
          {isLoading ? (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : prerequisites.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">
              Нет пререквизитов. Этот параграф не зависит от других тем.
            </p>
          ) : (
            prerequisites.map((prereq) => (
              <div
                key={prereq.id}
                className="flex items-center justify-between p-3 rounded-md border bg-background"
              >
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0" />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5">
                      <Badge variant="outline" className="text-xs shrink-0">
                        §{prereq.prerequisite_number}
                      </Badge>
                      {prereq.prerequisite_chapter_title && (
                        <span className="text-xs text-muted-foreground truncate">
                          {prereq.prerequisite_chapter_title}
                        </span>
                      )}
                    </div>
                    <p className="text-sm mt-0.5 truncate">
                      {prereq.prerequisite_title || `Параграф ${prereq.prerequisite_paragraph_id}`}
                    </p>
                    {isCrossTextbook(prereq) && (
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {prereq.prerequisite_textbook_title} ({prereq.prerequisite_grade_level} класс)
                      </p>
                    )}
                  </div>
                  <Badge
                    variant={STRENGTH_VARIANTS[prereq.strength] || 'outline'}
                    className="shrink-0"
                  >
                    {STRENGTH_LABELS[prereq.strength] || prereq.strength}
                  </Badge>
                </div>
                <div className="ml-2 shrink-0">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDelete(prereq)}
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Удалить пререквизит?</AlertDialogTitle>
            <AlertDialogDescription>
              Связь с §{prereqToDelete?.prerequisite_number}{' '}
              &quot;{prereqToDelete?.prerequisite_title}&quot; будет удалена.
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
    </>
  );
}
