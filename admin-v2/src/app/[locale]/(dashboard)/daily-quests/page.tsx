'use client';

import { useState } from 'react';
import {
  Plus,
  Pencil,
  Trash2,
} from 'lucide-react';
import { Card } from '@/components/ui/card';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
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

const QUEST_TYPES = [
  { value: 'complete_tests', label: 'Сдать тесты' },
  { value: 'study_time', label: 'Время учёбы' },
  { value: 'master_paragraph', label: 'Освоить параграф' },
  { value: 'review_spaced', label: 'Инт. повторение' },
];

const DEFAULT_FORM: DailyQuestCreate = {
  code: '',
  name_kk: '',
  name_ru: '',
  description_kk: '',
  description_ru: '',
  quest_type: 'complete_tests',
  target_value: 1,
  xp_reward: 0,
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
  const [form, setForm] = useState<DailyQuestCreate>(DEFAULT_FORM);

  // Cascading select state
  const [selectedTextbookId, setSelectedTextbookId] = useState<number | null>(null);
  const [selectedChapterId, setSelectedChapterId] = useState<number | null>(null);

  const { data: subjects } = useSubjects();
  const { data: textbooks } = useTextbooks();
  const { data: chapters } = useChapters(selectedTextbookId || 0, false, !!selectedTextbookId);
  const { data: paragraphs } = useParagraphs(selectedChapterId || 0, false, !!selectedChapterId);

  // Filter textbooks by selected subject
  const filteredTextbooks = form.subject_id
    ? textbooks?.filter((t) => t.subject_id === form.subject_id)
    : [];

  const canEdit = (quest: DailyQuestAdmin) => {
    if (isSuperAdmin) return quest.school_id === null;
    return quest.school_id !== null; // School admin can only edit own school quests
  };

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
      code: quest.code,
      name_kk: quest.name_kk,
      name_ru: quest.name_ru,
      description_kk: quest.description_kk || '',
      description_ru: quest.description_ru || '',
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
        const { code, ...updateData } = form;
        await updateQuest.mutateAsync({
          id: editingQuest.id,
          data: updateData,
        });
      } else {
        await createQuest.mutateAsync(form);
      }
      setDialogOpen(false);
    } catch {
      // Error handled by mutation hooks
    }
  };

  const handleDelete = async () => {
    if (deleteId) {
      await deleteQuest.mutateAsync(deleteId);
      setDeleteId(null);
    }
  };

  // Reset cascading selects when subject changes
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
    setForm((prev) => ({
      ...prev,
      textbook_id: textbookId,
      paragraph_id: null,
    }));
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
              Управление ежедневными заданиями для учеников
            </p>
          </div>
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4 mr-1" />
            Новый квест
          </Button>
        </div>

        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Код</TableHead>
                <TableHead>Название</TableHead>
                <TableHead>Тип</TableHead>
                <TableHead className="text-center">Цель</TableHead>
                <TableHead className="text-center">XP</TableHead>
                <TableHead>Предмет</TableHead>
                <TableHead>Область</TableHead>
                <TableHead>Статус</TableHead>
                <TableHead className="text-right">Действия</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {quests?.length === 0 && (
                <TableRow>
                  <TableCell colSpan={9} className="text-center text-muted-foreground py-8">
                    Нет квестов
                  </TableCell>
                </TableRow>
              )}
              {quests?.map((quest) => (
                <TableRow key={quest.id} className={!quest.is_active ? 'opacity-50' : ''}>
                  <TableCell className="font-mono text-sm">{quest.code}</TableCell>
                  <TableCell className="font-medium">{quest.name_ru}</TableCell>
                  <TableCell className="text-sm">
                    {QUEST_TYPES.find((t) => t.value === quest.quest_type)?.label || quest.quest_type}
                  </TableCell>
                  <TableCell className="text-center">{quest.target_value}</TableCell>
                  <TableCell className="text-center">{quest.xp_reward}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {quest.subject_name || '\u2014'}
                  </TableCell>
                  <TableCell>
                    <Badge variant={quest.school_id === null ? 'default' : 'secondary'}>
                      {quest.school_id === null ? 'Глобальный' : 'Школьный'}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={quest.is_active ? 'default' : 'outline'}>
                      {quest.is_active ? 'Активен' : 'Неактивен'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    {canEdit(quest) && (
                      <div className="flex justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => openEdit(quest)}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setDeleteId(quest.id)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>

        {/* Create/Edit Dialog */}
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {editingQuest ? 'Редактировать квест' : 'Новый квест'}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Код</Label>
                  <Input
                    value={form.code}
                    onChange={(e) => setForm({ ...form, code: e.target.value })}
                    placeholder="complete_5_tests"
                    disabled={!!editingQuest}
                  />
                </div>
                <div>
                  <Label>Тип</Label>
                  <Select
                    value={form.quest_type}
                    onValueChange={(v) => setForm({ ...form, quest_type: v })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {QUEST_TYPES.map((t) => (
                        <SelectItem key={t.value} value={t.value}>
                          {t.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Название (RU)</Label>
                  <Input
                    value={form.name_ru}
                    onChange={(e) => setForm({ ...form, name_ru: e.target.value })}
                    placeholder="Сдай 5 тестов"
                  />
                </div>
                <div>
                  <Label>Название (KK)</Label>
                  <Input
                    value={form.name_kk}
                    onChange={(e) => setForm({ ...form, name_kk: e.target.value })}
                    placeholder="5 тест тапсыр"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Описание (RU)</Label>
                  <Input
                    value={form.description_ru || ''}
                    onChange={(e) => setForm({ ...form, description_ru: e.target.value })}
                  />
                </div>
                <div>
                  <Label>Описание (KK)</Label>
                  <Input
                    value={form.description_kk || ''}
                    onChange={(e) => setForm({ ...form, description_kk: e.target.value })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Цель</Label>
                  <Input
                    type="number"
                    min={1}
                    value={form.target_value}
                    onChange={(e) =>
                      setForm({ ...form, target_value: parseInt(e.target.value) || 1 })
                    }
                  />
                </div>
                <div>
                  <Label>XP награда</Label>
                  <Input
                    type="number"
                    min={0}
                    value={form.xp_reward}
                    onChange={(e) =>
                      setForm({ ...form, xp_reward: parseInt(e.target.value) || 0 })
                    }
                  />
                </div>
                <div className="flex items-end gap-2 pb-1">
                  <Switch
                    checked={form.is_active}
                    onCheckedChange={(v) => setForm({ ...form, is_active: v })}
                  />
                  <Label>Активен</Label>
                </div>
              </div>

              {/* Cascading content selects */}
              <div className="border-t pt-4 space-y-3">
                <p className="text-sm font-medium text-muted-foreground">
                  Привязка к контенту (необязательно)
                </p>

                <div>
                  <Label>Предмет</Label>
                  <Select
                    value={form.subject_id ? form.subject_id.toString() : 'none'}
                    onValueChange={handleSubjectChange}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Любой предмет" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Любой предмет</SelectItem>
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
                    <Label>Учебник</Label>
                    <Select
                      value={form.textbook_id ? form.textbook_id.toString() : 'none'}
                      onValueChange={handleTextbookChange}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Любой учебник" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">Любой учебник</SelectItem>
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
                    <Label>Глава</Label>
                    <Select
                      value={selectedChapterId ? selectedChapterId.toString() : 'none'}
                      onValueChange={handleChapterChange}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Выберите главу" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">{'\u2014'}</SelectItem>
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
                    <Label>Параграф</Label>
                    <Select
                      value={form.paragraph_id ? form.paragraph_id.toString() : 'none'}
                      onValueChange={handleParagraphChange}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Любой параграф" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">Любой параграф</SelectItem>
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
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogOpen(false)}>
                Отмена
              </Button>
              <Button
                onClick={handleSave}
                disabled={
                  !form.code || !form.name_ru || !form.name_kk ||
                  createQuest.isPending || updateQuest.isPending
                }
              >
                {editingQuest ? 'Сохранить' : 'Создать'}
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
                Квест будет деактивирован и не будет назначаться ученикам.
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
