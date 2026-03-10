'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useEffect, useState, useMemo } from 'react';
import { Loader2, ChevronsUpDown, Check, X } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
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
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  paragraphCreateSchema,
  paragraphCreateDefaults,
  type ParagraphCreateInput,
  type ParagraphUpdateInput,
} from '@/lib/validations/textbook';
import { useOutcomes, useFrameworks, useSections } from '@/lib/hooks/use-goso';
import type { Paragraph } from '@/types';
import { EmbeddedQuestionsSection } from './embedded-questions-section';
import { PrerequisitesSection } from './prerequisites-section';

interface ParagraphDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  chapterId: number;
  chapterNumber?: number;
  paragraph?: Paragraph;
  nextNumber: number;
  onSubmit: (data: ParagraphCreateInput | ParagraphUpdateInput) => void;
  isLoading?: boolean;
  isFetchingParagraph?: boolean;
  isSchool?: boolean;
  gradeLevel?: number;
  subjectId?: number | null;
  textbookId?: number;
}

export function ParagraphDialog({
  open,
  onOpenChange,
  chapterId,
  chapterNumber,
  paragraph,
  nextNumber,
  onSubmit,
  isLoading,
  isFetchingParagraph,
  isSchool = false,
  gradeLevel,
  subjectId,
  textbookId,
}: ParagraphDialogProps) {
  const isEditing = !!paragraph;
  const [outcomePopoverOpen, setOutcomePopoverOpen] = useState(false);

  const hasGosoFilters = !!(gradeLevel && subjectId);

  // Load frameworks for this subject to find section_id matching chapter number
  const { data: frameworks = [] } = useFrameworks(
    hasGosoFilters ? subjectId! : undefined
  );
  const frameworkId = frameworks.length > 0 ? frameworks[0].id : undefined;

  const { data: sections = [] } = useSections(
    frameworkId ?? 0,
    !!frameworkId && open
  );

  // Match chapter number to GOSO section by code or display_order
  const matchedSectionId = useMemo(() => {
    if (!chapterNumber || sections.length === 0) return undefined;
    const byCode = sections.find((s) => s.code === String(chapterNumber));
    if (byCode) return byCode.id;
    const byOrder = sections.find((s) => s.display_order === chapterNumber);
    if (byOrder) return byOrder.id;
    return undefined;
  }, [chapterNumber, sections]);

  const outcomeParams = useMemo(() => {
    if (!hasGosoFilters) return undefined;
    const params: { grade: number; subject_id: number; section_id?: number } = {
      grade: gradeLevel!,
      subject_id: subjectId!,
    };
    if (matchedSectionId) {
      params.section_id = matchedSectionId;
    }
    return params;
  }, [hasGosoFilters, gradeLevel, subjectId, matchedSectionId]);

  const { data: outcomes = [] } = useOutcomes(
    outcomeParams,
    hasGosoFilters && open
  );

  const form = useForm<ParagraphCreateInput>({
    resolver: zodResolver(paragraphCreateSchema),
    defaultValues: paragraph
      ? {
          chapter_id: paragraph.chapter_id,
          title: paragraph.title,
          number: paragraph.number,
          order: paragraph.order,
          content: paragraph.content,
          summary: paragraph.summary || '',
          learning_objective: paragraph.learning_objective || '',
          lesson_objective: paragraph.lesson_objective || '',
          key_terms: paragraph.key_terms || [],
          questions: paragraph.questions || [],
        }
      : paragraphCreateDefaults(chapterId, nextNumber),
  });

  // Reset form when dialog opens/closes or paragraph changes
  useEffect(() => {
    if (open) {
      if (paragraph) {
        form.reset({
          chapter_id: paragraph.chapter_id,
          title: paragraph.title,
          number: paragraph.number,
          order: paragraph.order,
          content: paragraph.content,
          summary: paragraph.summary || '',
          learning_objective: paragraph.learning_objective || '',
          lesson_objective: paragraph.lesson_objective || '',
          key_terms: paragraph.key_terms || [],
          questions: paragraph.questions || [],
        });
      } else {
        form.reset(paragraphCreateDefaults(chapterId, nextNumber));
      }
    }
  }, [open, paragraph, chapterId, nextNumber, form]);

  const handleSubmit = (data: ParagraphCreateInput) => {
    if (isEditing) {
      // For update, exclude chapter_id
      const { chapter_id, ...updateData } = data;
      onSubmit(updateData);
    } else {
      onSubmit(data);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? 'Редактировать параграф' : 'Добавить параграф'}
          </DialogTitle>
          <DialogDescription>
            {isEditing
              ? 'Измените данные параграфа'
              : 'Заполните информацию о новом параграфе'}
          </DialogDescription>
        </DialogHeader>

        {isFetchingParagraph ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="number"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Номер параграфа *</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={1}
                        {...field}
                        onChange={(e) => field.onChange(parseInt(e.target.value) || 1)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="order"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Порядок</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={0}
                        {...field}
                        onChange={(e) => field.onChange(parseInt(e.target.value) || 0)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Название *</FormLabel>
                  <FormControl>
                    <Input placeholder="Линейные уравнения" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="summary"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Краткое содержание</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Краткое описание параграфа..."
                      className="min-h-[60px]"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="content"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Содержание *</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Текст параграфа..."
                      className="min-h-[200px]"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="learning_objective"
              render={({ field }) => (
                <FormItem className="flex flex-col">
                  <FormLabel>Цель обучения</FormLabel>
                  {hasGosoFilters && outcomes.length > 0 ? (
                    <>
                      <Popover open={outcomePopoverOpen} onOpenChange={setOutcomePopoverOpen}>
                        <PopoverTrigger asChild>
                          <FormControl>
                            <Button
                              variant="outline"
                              role="combobox"
                              aria-expanded={outcomePopoverOpen}
                              className="justify-between h-auto min-h-[40px] font-normal text-left whitespace-normal"
                            >
                              {field.value ? (
                                <span className="line-clamp-2 text-sm">{field.value}</span>
                              ) : (
                                <span className="text-muted-foreground">Выберите цель обучения...</span>
                              )}
                              <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                            </Button>
                          </FormControl>
                        </PopoverTrigger>
                        <PopoverContent
                          className="w-[500px] p-0"
                          align="start"
                          side="bottom"
                          sideOffset={4}
                          onOpenAutoFocus={(e) => e.preventDefault()}
                        >
                          <Command>
                            <CommandInput placeholder="Поиск цели обучения..." />
                            <CommandList style={{ maxHeight: '250px', overflowY: 'auto' }}>
                              <CommandEmpty>Ничего не найдено</CommandEmpty>
                              <CommandGroup>
                                {outcomes.map((outcome) => (
                                  <CommandItem
                                    key={outcome.id}
                                    value={`${outcome.code} ${outcome.title_ru}`}
                                    onSelect={() => {
                                      field.onChange(outcome.title_ru);
                                      setOutcomePopoverOpen(false);
                                    }}
                                  >
                                    <Check
                                      className={`mr-2 h-4 w-4 shrink-0 ${
                                        field.value === outcome.title_ru ? 'opacity-100' : 'opacity-0'
                                      }`}
                                    />
                                    <div className="flex-1 min-w-0">
                                      <div className="flex items-center gap-1.5">
                                        <Badge variant="outline" className="text-xs shrink-0">
                                          {outcome.code}
                                        </Badge>
                                        {outcome.cognitive_level && (
                                          <Badge variant="secondary" className="text-xs shrink-0">
                                            {outcome.cognitive_level}
                                          </Badge>
                                        )}
                                      </div>
                                      <p className="text-sm mt-1">{outcome.title_ru}</p>
                                    </div>
                                  </CommandItem>
                                ))}
                              </CommandGroup>
                            </CommandList>
                          </Command>
                        </PopoverContent>
                      </Popover>
                      {field.value && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="self-start h-auto p-1 text-xs text-muted-foreground"
                          onClick={() => field.onChange('')}
                        >
                          <X className="h-3 w-3 mr-1" />
                          Очистить
                        </Button>
                      )}
                    </>
                  ) : (
                    <FormControl>
                      <Textarea
                        placeholder="Что ученик должен узнать..."
                        className="min-h-[80px]"
                        {...field}
                      />
                    </FormControl>
                  )}
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="lesson_objective"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Цель урока</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Цель конкретного урока..."
                      className="min-h-[80px]"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Embedded Questions Section (only when editing existing paragraph) */}
            {isEditing && paragraph && (
              <EmbeddedQuestionsSection
                paragraphId={paragraph.id}
                isSchool={isSchool}
              />
            )}

            {/* Prerequisites Section (only when editing global paragraphs) */}
            {isEditing && paragraph && !isSchool && textbookId && (
              <PrerequisitesSection
                paragraphId={paragraph.id}
                textbookId={textbookId}
                subjectId={subjectId}
              />
            )}

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                Отмена
              </Button>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? 'Сохранение...' : isEditing ? 'Сохранить' : 'Создать'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
        )}
      </DialogContent>
    </Dialog>
  );
}
