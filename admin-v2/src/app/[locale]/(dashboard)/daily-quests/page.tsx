'use client';

import { useState, useMemo } from 'react';
import {
  Plus,
  Pencil,
  Trash2,
  Zap,
  BookOpen,
  Target,
  Clock,
  RefreshCw,
  Trophy,
  Info,
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Switch } from '@/components/ui/switch';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
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
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { RoleGuard } from '@/components/auth';
import { useAuth } from '@/providers/auth-provider';
import {
  useDailyQuests,
  useCreateDailyQuest,
  useUpdateDailyQuest,
  useDeleteDailyQuest,
} from '@/lib/hooks/use-daily-quests';
import { useSubjects } from '@/lib/hooks/use-goso';
import { useTextbooks, useChapters, useParagraphs } from '@/lib/hooks/use-textbooks';
import type { DailyQuestAdmin, DailyQuestCreate } from '@/lib/api/daily-quests';

// ── Quest type config with icons, descriptions, and unit labels ──

const QUEST_TYPE_CONFIG = [
  {
    value: 'complete_tests',
    label: 'Сдать тесты',
    icon: Target,
    description: 'Ученик должен сдать определённое количество тестов',
    unit: 'тестов',
    defaultTarget: 3,
    defaultXp: 30,
  },
  {
    value: 'master_paragraph',
    label: 'Освоить параграф',
    icon: BookOpen,
    description: 'Ученик должен полностью освоить параграфы (статус mastered)',
    unit: 'параграфов',
    defaultTarget: 1,
    defaultXp: 40,
  },
  {
    value: 'study_time',
    label: 'Время учёбы',
    icon: Clock,
    description: 'Ученик проводит определённое время за учёбой (в минутах)',
    unit: 'минут',
    defaultTarget: 30,
    defaultXp: 25,
  },
  {
    value: 'review_spaced',
    label: 'Интервальное повторение',
    icon: RefreshCw,
    description: 'Ученик выполняет интервальные повторения пройденного материала',
    unit: 'повторений',
    defaultTarget: 2,
    defaultXp: 20,
  },
];

// ── Auto-generate code from quest type + target + subject ──

function generateCode(questType: string, target: number, subjectCode?: string): string {
  const typeShort = questType.replace('complete_', '').replace('master_', 'master_');
  const suffix = subjectCode ? `_${subjectCode}` : '';
  return `${typeShort}_${target}${suffix}`;
}

// ── Default form state ──

interface QuestFormState {
  name_ru: string;
  name_kk: string;
  description_ru: string;
  description_kk: string;
  quest_type: string;
  target_value: number;
  xp_reward: number;
  is_active: boolean;
  subject_id: number | null;
  textbook_id: number | null;
  paragraph_id: number | null;
}

const DEFAULT_FORM: QuestFormState = {
  name_ru: '',
  name_kk: '',
  description_ru: '',
  description_kk: '',
  quest_type: 'complete_tests',
  target_value: 3,
  xp_reward: 30,
  is_active: true,
  subject_id: null,
  textbook_id: null,
  paragraph_id: null,
};

export default function DailyQuestsPage() {
  const { user, isSuperAdmin } = useAuth();
  const role = user?.role || 'admin';
  const { data: quests, isLoading } = useDailyQuests(role);
  const createQuest = useCreateDailyQuest(role);
  const updateQuest = useUpdateDailyQuest(role);
  const deleteQuest = useDeleteDailyQuest(role);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingQuest, setEditingQuest] = useState<DailyQuestAdmin | null>(null);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [form, setForm] = useState<QuestFormState>(DEFAULT_FORM);

  // Cascading select state
  const [selectedTextbookId, setSelectedTextbookId] = useState<number | null>(null);
  const [selectedChapterId, setSelectedChapterId] = useState<number | null>(null);

  const { data: subjects } = useSubjects();
  const { data: textbooks } = useTextbooks();
  const { data: chapters } = useChapters(selectedTextbookId || 0, false, !!selectedTextbookId);
  const { data: paragraphs } = useParagraphs(selectedChapterId || 0, false, !!selectedChapterId);

  const filteredTextbooks = form.subject_id
    ? textbooks?.filter((t) => t.subject_id === form.subject_id)
    : [];

  const selectedSubject = useMemo(
    () => subjects?.find((s) => s.id === form.subject_id),
    [subjects, form.subject_id]
  );

  const currentTypeConfig = useMemo(
    () => QUEST_TYPE_CONFIG.find((t) => t.value === form.quest_type) || QUEST_TYPE_CONFIG[0],
    [form.quest_type]
  );

  const canEdit = (quest: DailyQuestAdmin) => {
    if (isSuperAdmin) return quest.school_id === null;
    return quest.school_id !== null;
  };

  // ── Handlers ──

  const openCreate = () => {
    setEditingQuest(null);
    setForm(DEFAULT_FORM);
    setSelectedTextbookId(null);
    setSelectedChapterId(null);
    setDialogOpen(true);
  };

  const openEdit = (quest: DailyQuestAdmin) => {
    setEditingQuest(quest);
    setForm({
      name_ru: quest.name_ru,
      name_kk: quest.name_kk,
      description_ru: quest.description_ru || '',
      description_kk: quest.description_kk || '',
      quest_type: quest.quest_type,
      target_value: quest.target_value,
      xp_reward: quest.xp_reward,
      is_active: quest.is_active,
      subject_id: quest.subject_id,
      textbook_id: quest.textbook_id,
      paragraph_id: quest.paragraph_id,
    });
    setSelectedTextbookId(quest.textbook_id);
    setSelectedChapterId(null);
    setDialogOpen(true);
  };

  const handleSave = async () => {
    try {
      if (editingQuest) {
        await updateQuest.mutateAsync({ id: editingQuest.id, data: form });
      } else {
        const code = generateCode(
          form.quest_type,
          form.target_value,
          selectedSubject?.code
        );
        const payload: DailyQuestCreate = { ...form, code };
        await createQuest.mutateAsync(payload);
      }
      setDialogOpen(false);
    } catch {
      // handled by mutation hooks
    }
  };

  const handleDelete = async () => {
    if (deleteId) {
      await deleteQuest.mutateAsync(deleteId);
      setDeleteId(null);
    }
  };

  const handleQuestTypeChange = (value: string) => {
    const config = QUEST_TYPE_CONFIG.find((t) => t.value === value) || QUEST_TYPE_CONFIG[0];
    setForm((prev) => ({
      ...prev,
      quest_type: value,
      target_value: config.defaultTarget,
      xp_reward: config.defaultXp,
      // Auto-fill names if empty
      name_ru: prev.name_ru || '',
      name_kk: prev.name_kk || '',
    }));
  };

  const handleSubjectChange = (value: string) => {
    const subjectId = value === 'none' ? null : parseInt(value);
    setForm((prev) => ({
      ...prev,
      subject_id: subjectId,
      textbook_id: null,
      paragraph_id: null,
    }));
    setSelectedTextbookId(null);
    setSelectedChapterId(null);
  };

  const handleTextbookChange = (value: string) => {
    const textbookId = value === 'none' ? null : parseInt(value);
    setForm((prev) => ({ ...prev, textbook_id: textbookId, paragraph_id: null }));
    setSelectedTextbookId(textbookId);
    setSelectedChapterId(null);
  };

  const handleChapterChange = (value: string) => {
    const chapterId = value === 'none' ? null : parseInt(value);
    setSelectedChapterId(chapterId);
    setForm((prev) => ({ ...prev, paragraph_id: null }));
  };

  const handleParagraphChange = (value: string) => {
    const paragraphId = value === 'none' ? null : parseInt(value);
    setForm((prev) => ({ ...prev, paragraph_id: paragraphId }));
  };

  // ── Form validation ──

  const isFormValid = form.name_ru.trim() && form.name_kk.trim() && form.target_value > 0;

  // ── Render ──

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  return (
    <RoleGuard allowedRoles={['super_admin', 'admin']}>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Ежедневные квесты</h1>
            <p className="text-muted-foreground">
              Задания, которые ученики выполняют каждый день за XP
            </p>
          </div>
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4 mr-1" />
            Новый квест
          </Button>
        </div>

        {/* Quest cards grid for better readability */}
        {quests?.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-16 text-center">
              <Zap className="h-12 w-12 text-muted-foreground/30 mb-4" />
              <p className="text-lg font-medium text-muted-foreground">Нет квестов</p>
              <p className="text-sm text-muted-foreground/70 mt-1">
                Создайте первый ежедневный квест для учеников
              </p>
              <Button onClick={openCreate} className="mt-4" variant="outline">
                <Plus className="h-4 w-4 mr-1" />
                Создать квест
              </Button>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Квест</TableHead>
                  <TableHead>Тип</TableHead>
                  <TableHead className="text-center">Цель</TableHead>
                  <TableHead className="text-center">XP</TableHead>
                  <TableHead>Предмет</TableHead>
                  <TableHead>Статус</TableHead>
                  <TableHead className="text-right">Действия</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {quests?.map((quest) => {
                  const typeConfig = QUEST_TYPE_CONFIG.find((t) => t.value === quest.quest_type);
                  const TypeIcon = typeConfig?.icon || Target;
                  return (
                    <TableRow key={quest.id} className={!quest.is_active ? 'opacity-50' : ''}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                            <TypeIcon className="h-4 w-4 text-primary" />
                          </div>
                          <div className="min-w-0">
                            <p className="font-medium truncate">{quest.name_ru}</p>
                            <p className="text-xs text-muted-foreground truncate">
                              {quest.description_ru || quest.name_kk}
                            </p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell className="text-sm">
                        {typeConfig?.label || quest.quest_type}
                      </TableCell>
                      <TableCell className="text-center font-medium">
                        {quest.target_value}
                        <span className="text-xs text-muted-foreground ml-1">
                          {typeConfig?.unit || ''}
                        </span>
                      </TableCell>
                      <TableCell className="text-center">
                        <span className="inline-flex items-center gap-1 font-medium text-amber-600">
                          <Trophy className="h-3 w-3" />
                          {quest.xp_reward}
                        </span>
                      </TableCell>
                      <TableCell className="text-sm">
                        {quest.subject_name ? (
                          <Badge variant="outline">{quest.subject_name}</Badge>
                        ) : (
                          <span className="text-muted-foreground">Все предметы</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Badge variant={quest.is_active ? 'default' : 'outline'}>
                            {quest.is_active ? 'Активен' : 'Неактивен'}
                          </Badge>
                          {quest.school_id !== null && (
                            <Badge variant="secondary">Школьный</Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        {canEdit(quest) ? (
                          <div className="flex justify-end gap-1">
                            <Button variant="ghost" size="icon" onClick={() => openEdit(quest)}>
                              <Pencil className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="icon" onClick={() => setDeleteId(quest.id)}>
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          </div>
                        ) : (
                          <span className="text-xs text-muted-foreground">Только чтение</span>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </Card>
        )}

        {/* ── Create/Edit Dialog ── */}
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {editingQuest ? 'Редактировать квест' : 'Новый ежедневный квест'}
              </DialogTitle>
              <DialogDescription>
                {editingQuest
                  ? 'Измените параметры квеста'
                  : 'Квест назначается ученикам каждый день. Прогресс отслеживается автоматически.'}
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-5">
              {/* Step 1: Quest Type — visual cards */}
              <div>
                <Label className="text-sm font-medium mb-2 block">Что должен сделать ученик?</Label>
                <div className="grid grid-cols-2 gap-2">
                  {QUEST_TYPE_CONFIG.map((type) => {
                    const Icon = type.icon;
                    const isSelected = form.quest_type === type.value;
                    return (
                      <button
                        key={type.value}
                        type="button"
                        onClick={() => handleQuestTypeChange(type.value)}
                        className={`flex items-start gap-3 rounded-lg border p-3 text-left transition-all ${
                          isSelected
                            ? 'border-primary bg-primary/5 ring-1 ring-primary'
                            : 'border-border hover:border-primary/40 hover:bg-muted/50'
                        }`}
                      >
                        <Icon className={`h-5 w-5 mt-0.5 shrink-0 ${isSelected ? 'text-primary' : 'text-muted-foreground'}`} />
                        <div className="min-w-0">
                          <p className={`text-sm font-medium ${isSelected ? 'text-primary' : ''}`}>
                            {type.label}
                          </p>
                          <p className="text-[11px] text-muted-foreground leading-tight mt-0.5">
                            {type.description}
                          </p>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Step 2: Target + XP */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm">
                    Сколько {currentTypeConfig.unit}?
                  </Label>
                  <div className="relative mt-1">
                    <Input
                      type="number"
                      min={1}
                      value={form.target_value}
                      onChange={(e) =>
                        setForm({ ...form, target_value: parseInt(e.target.value) || 1 })
                      }
                      className="pr-16"
                    />
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">
                      {currentTypeConfig.unit}
                    </span>
                  </div>
                </div>
                <div>
                  <Label className="text-sm flex items-center gap-1">
                    Награда XP
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger>
                          <Info className="h-3.5 w-3.5 text-muted-foreground" />
                        </TooltipTrigger>
                        <TooltipContent>
                          <p className="max-w-48">Очки опыта, которые ученик получит за выполнение квеста</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </Label>
                  <div className="relative mt-1">
                    <Input
                      type="number"
                      min={0}
                      value={form.xp_reward}
                      onChange={(e) =>
                        setForm({ ...form, xp_reward: parseInt(e.target.value) || 0 })
                      }
                      className="pr-10"
                    />
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">
                      XP
                    </span>
                  </div>
                </div>
              </div>

              {/* Step 3: Names */}
              <div className="space-y-3">
                <div>
                  <Label className="text-sm">Название (RU)</Label>
                  <Input
                    value={form.name_ru}
                    onChange={(e) => setForm({ ...form, name_ru: e.target.value })}
                    placeholder={`Например: Сдай ${form.target_value} ${currentTypeConfig.unit}`}
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label className="text-sm">Название (KK)</Label>
                  <Input
                    value={form.name_kk}
                    onChange={(e) => setForm({ ...form, name_kk: e.target.value })}
                    placeholder={`Мысалы: ${form.target_value} ${currentTypeConfig.unit} орында`}
                    className="mt-1"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-sm text-muted-foreground">Описание (RU)</Label>
                    <Input
                      value={form.description_ru}
                      onChange={(e) => setForm({ ...form, description_ru: e.target.value })}
                      placeholder="Необязательно"
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-sm text-muted-foreground">Описание (KK)</Label>
                    <Input
                      value={form.description_kk}
                      onChange={(e) => setForm({ ...form, description_kk: e.target.value })}
                      placeholder="Міндетті емес"
                      className="mt-1"
                    />
                  </div>
                </div>
              </div>

              {/* Step 4: Content binding (collapsible) */}
              <div className="rounded-lg border bg-muted/30 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">Привязка к предмету</p>
                    <p className="text-xs text-muted-foreground">
                      Квест будет засчитываться только по выбранному предмету
                    </p>
                  </div>
                </div>

                <div>
                  <Select
                    value={form.subject_id ? form.subject_id.toString() : 'none'}
                    onValueChange={handleSubjectChange}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Все предметы" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Все предметы (без ограничений)</SelectItem>
                      {subjects?.map((s) => (
                        <SelectItem key={s.id} value={s.id.toString()}>
                          {s.name_ru}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {form.subject_id && (
                  <div>
                    <Label className="text-xs text-muted-foreground">Учебник (необязательно)</Label>
                    <Select
                      value={form.textbook_id ? form.textbook_id.toString() : 'none'}
                      onValueChange={handleTextbookChange}
                    >
                      <SelectTrigger className="mt-1">
                        <SelectValue placeholder="Любой учебник" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">Любой учебник этого предмета</SelectItem>
                        {filteredTextbooks?.map((t) => (
                          <SelectItem key={t.id} value={t.id.toString()}>
                            {t.title}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}

                {selectedTextbookId && (
                  <div>
                    <Label className="text-xs text-muted-foreground">Глава</Label>
                    <Select
                      value={selectedChapterId ? selectedChapterId.toString() : 'none'}
                      onValueChange={handleChapterChange}
                    >
                      <SelectTrigger className="mt-1">
                        <SelectValue placeholder="Выберите главу" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">Не выбрано</SelectItem>
                        {chapters?.map((c) => (
                          <SelectItem key={c.id} value={c.id.toString()}>
                            {c.title}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}

                {selectedChapterId && (
                  <div>
                    <Label className="text-xs text-muted-foreground">Параграф (необязательно)</Label>
                    <Select
                      value={form.paragraph_id ? form.paragraph_id.toString() : 'none'}
                      onValueChange={handleParagraphChange}
                    >
                      <SelectTrigger className="mt-1">
                        <SelectValue placeholder="Любой параграф" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">Любой параграф этой главы</SelectItem>
                        {paragraphs?.map((p) => (
                          <SelectItem key={p.id} value={p.id.toString()}>
                            {p.title}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}
              </div>

              {/* Active toggle */}
              {editingQuest && (
                <div className="flex items-center justify-between rounded-lg border p-3">
                  <div>
                    <p className="text-sm font-medium">Квест активен</p>
                    <p className="text-xs text-muted-foreground">
                      Неактивные квесты не назначаются ученикам
                    </p>
                  </div>
                  <Switch
                    checked={form.is_active}
                    onCheckedChange={(v) => setForm({ ...form, is_active: v })}
                  />
                </div>
              )}

              {/* Preview */}
              <div className="rounded-lg border-2 border-dashed border-primary/20 bg-primary/5 p-4">
                <p className="text-xs font-medium text-primary mb-2">Предпросмотр квеста ученика:</p>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold">
                      {form.name_ru || `Сдай ${form.target_value} ${currentTypeConfig.unit}`}
                    </p>
                    {form.description_ru && (
                      <p className="text-xs text-muted-foreground">{form.description_ru}</p>
                    )}
                    {selectedSubject && (
                      <Badge variant="outline" className="mt-1 text-[10px]">
                        {selectedSubject.name_ru}
                      </Badge>
                    )}
                  </div>
                  <span className="text-xs font-bold text-amber-600 whitespace-nowrap">
                    +{form.xp_reward} XP
                  </span>
                </div>
                <div className="mt-2 h-2 rounded-full bg-primary/10">
                  <div className="h-2 rounded-full bg-primary/40 w-1/3" />
                </div>
                <p className="text-[10px] text-muted-foreground mt-1">
                  0 / {form.target_value} {currentTypeConfig.unit}
                </p>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogOpen(false)}>
                Отмена
              </Button>
              <Button
                onClick={handleSave}
                disabled={!isFormValid || createQuest.isPending || updateQuest.isPending}
              >
                {createQuest.isPending || updateQuest.isPending ? 'Сохранение...' : editingQuest ? 'Сохранить' : 'Создать квест'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Delete confirmation */}
        <AlertDialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Деактивировать квест?</AlertDialogTitle>
              <AlertDialogDescription>
                Квест будет деактивирован и больше не будет назначаться ученикам. Уже назначенные квесты сохранятся.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Отмена</AlertDialogCancel>
              <AlertDialogAction onClick={handleDelete}>
                Деактивировать
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </RoleGuard>
  );
}
