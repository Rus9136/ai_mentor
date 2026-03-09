'use client';

import { useState, useMemo } from 'react';
import { Plus, Trash2, Loader2, GitBranch, Check, ChevronsUpDown, ArrowRight } from 'lucide-react';

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
import { useChapters, useParagraphs } from '@/lib/hooks/use-textbooks';
import type { Paragraph } from '@/types';
import type { PrerequisiteResponse } from '@/lib/api/prerequisites';

interface PrerequisitesSectionProps {
  paragraphId: number;
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
}: PrerequisitesSectionProps) {
  const { data: prerequisites = [], isLoading } = usePrerequisites(paragraphId);
  const createMutation = useCreatePrerequisite();
  const deleteMutation = useDeletePrerequisite();

  // Load all chapters and their paragraphs for the picker
  const { data: chapters = [] } = useChapters(textbookId, false);

  const [pickerOpen, setPickerOpen] = useState(false);
  const [strength, setStrength] = useState<string>('required');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [prereqToDelete, setPrereqToDelete] = useState<PrerequisiteResponse | null>(null);

  // Build flat list of all paragraphs across all chapters for the picker
  // We need to load paragraphs for each chapter
  const [allParagraphs, setAllParagraphs] = useState<
    Array<{ paragraph: Paragraph; chapterTitle: string }>
  >([]);
  const [paragraphsLoaded, setParagraphsLoaded] = useState(false);

  // Load paragraphs when picker opens
  const loadAllParagraphs = async () => {
    if (paragraphsLoaded || chapters.length === 0) return;

    // Use the textbooks API directly to get paragraphs per chapter
    const { textbooksApi } = await import('@/lib/api/textbooks');
    const allParas: Array<{ paragraph: Paragraph; chapterTitle: string }> = [];

    for (const chapter of chapters) {
      try {
        const paragraphs = await textbooksApi.getParagraphs(chapter.id, false);
        for (const p of paragraphs) {
          allParas.push({
            paragraph: p,
            chapterTitle: chapter.title || `Глава ${chapter.number}`,
          });
        }
      } catch {
        // Skip chapters with errors
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
                  className="w-[450px] p-0"
                  align="end"
                  side="bottom"
                  sideOffset={4}
                  onOpenAutoFocus={(e) => e.preventDefault()}
                >
                  <Command>
                    <CommandInput placeholder="Поиск параграфа..." />
                    <CommandList style={{ maxHeight: '300px', overflowY: 'auto' }}>
                      {!paragraphsLoaded ? (
                        <div className="flex items-center justify-center py-6">
                          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                        </div>
                      ) : availableParagraphs.length === 0 ? (
                        <CommandEmpty>Нет доступных параграфов</CommandEmpty>
                      ) : (
                        <CommandGroup>
                          {availableParagraphs.map(({ paragraph: p, chapterTitle }) => (
                            <CommandItem
                              key={p.id}
                              value={`§${p.number} ${p.title} ${chapterTitle}`}
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
