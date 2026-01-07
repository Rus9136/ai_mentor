'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useTranslations, useLocale } from 'next-intl';
import Link from 'next/link';
import {
  ArrowLeft,
  Loader2,
  Save,
  Trash2,
  Send,
  Plus,
  Sparkles,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
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
import {
  HomeworkStatusBadge,
  TaskTypeSelector,
  ContentSelector,
  AIGenerationPanel,
  QuestionCard,
} from '@/components/homework';
import { useClasses } from '@/lib/hooks/use-teacher-data';
import {
  useHomework,
  useUpdateHomework,
  useDeleteHomework,
  usePublishHomework,
  useAddTask,
  useDeleteTask,
  useGenerateQuestions,
} from '@/lib/hooks/use-homework';
import { HomeworkStatus, TaskType, type GenerationParams } from '@/types/homework';

export default function EditHomeworkPage() {
  const params = useParams();
  const router = useRouter();
  const locale = useLocale();
  const t = useTranslations('homework');
  const tCommon = useTranslations('common');

  const homeworkId = Number(params.id);

  // Data loading
  const { data: homework, isLoading, error } = useHomework(homeworkId);
  const { data: classes } = useClasses();

  // Mutations
  const updateHomework = useUpdateHomework();
  const deleteHomework = useDeleteHomework();
  const publishHomework = usePublishHomework();
  const addTask = useAddTask();
  const deleteTask = useDeleteTask();
  const generateQuestions = useGenerateQuestions();

  // Form state
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [targetDifficulty, setTargetDifficulty] = useState<'easy' | 'medium' | 'hard' | 'auto'>('auto');
  const [aiGenerationEnabled, setAiGenerationEnabled] = useState(true);
  const [aiCheckEnabled, setAiCheckEnabled] = useState(true);

  // UI state
  const [isDirty, setIsDirty] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showAddTaskForm, setShowAddTaskForm] = useState(false);
  const [expandedTasks, setExpandedTasks] = useState<Set<number>>(new Set());
  const [generatingTaskId, setGeneratingTaskId] = useState<number | null>(null);
  const [deletingTaskId, setDeletingTaskId] = useState<number | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  // New task form state
  const [newTaskType, setNewTaskType] = useState<TaskType>(TaskType.QUIZ);
  const [newTaskParagraphId, setNewTaskParagraphId] = useState<number | null>(null);
  const [newTaskChapterId, setNewTaskChapterId] = useState<number | null>(null);
  const [newTaskPoints, setNewTaskPoints] = useState(10);
  const [newTaskMaxAttempts, setNewTaskMaxAttempts] = useState(1);
  const [newTaskInstructions, setNewTaskInstructions] = useState('');

  // Initialize form from homework data
  useEffect(() => {
    if (homework) {
      // Redirect if not draft
      if (homework.status !== HomeworkStatus.DRAFT) {
        router.replace(`/${locale}/homework/${homeworkId}`);
        return;
      }

      setTitle(homework.title);
      setDescription(homework.description || '');
      setDueDate(formatDateForInput(homework.due_date));
      setTargetDifficulty(homework.target_difficulty as any || 'auto');
      setAiGenerationEnabled(homework.ai_generation_enabled);
      setAiCheckEnabled(homework.ai_check_enabled);

      // Expand all tasks by default
      setExpandedTasks(new Set(homework.tasks.map(t => t.id)));
    }
  }, [homework, homeworkId, locale, router]);

  // Track dirty state
  useEffect(() => {
    if (!homework) return;

    const dirty =
      title !== homework.title ||
      description !== (homework.description || '') ||
      dueDate !== formatDateForInput(homework.due_date) ||
      targetDifficulty !== (homework.target_difficulty || 'auto') ||
      aiGenerationEnabled !== homework.ai_generation_enabled ||
      aiCheckEnabled !== homework.ai_check_enabled;

    setIsDirty(dirty);
  }, [homework, title, description, dueDate, targetDifficulty, aiGenerationEnabled, aiCheckEnabled]);

  // Helper: Format date for datetime-local input
  function formatDateForInput(isoDate: string): string {
    const date = new Date(isoDate);
    const offset = date.getTimezoneOffset();
    const localDate = new Date(date.getTime() - offset * 60 * 1000);
    return localDate.toISOString().slice(0, 16);
  }

  // Save basic info
  const handleSave = async () => {
    if (!title.trim()) {
      setFormError(t('errors.noTitle'));
      return;
    }

    setIsSaving(true);
    setFormError(null);

    try {
      await updateHomework.mutateAsync({
        homeworkId,
        data: {
          title: title.trim(),
          description: description.trim() || undefined,
          due_date: new Date(dueDate).toISOString(),
          target_difficulty: targetDifficulty,
          ai_generation_enabled: aiGenerationEnabled,
          ai_check_enabled: aiCheckEnabled,
        },
      });
      setIsDirty(false);
    } catch {
      setFormError(t('errors.updateFailed'));
    } finally {
      setIsSaving(false);
    }
  };

  // Delete draft
  const handleDelete = async () => {
    try {
      await deleteHomework.mutateAsync(homeworkId);
      router.push(`/${locale}/homework`);
    } catch {
      setFormError(t('errors.updateFailed'));
    }
  };

  // Publish homework
  const handlePublish = async () => {
    try {
      await publishHomework.mutateAsync({ homeworkId });
      router.push(`/${locale}/homework/${homeworkId}`);
    } catch {
      setFormError(t('errors.publishFailed'));
    }
  };

  // Add new task
  const handleAddTask = async () => {
    if (!newTaskParagraphId && !newTaskChapterId) {
      setFormError(t('task.selectParagraph'));
      return;
    }

    setFormError(null);

    try {
      await addTask.mutateAsync({
        homeworkId,
        data: {
          paragraph_id: newTaskParagraphId || undefined,
          chapter_id: newTaskChapterId || undefined,
          task_type: newTaskType,
          points: newTaskPoints,
          max_attempts: newTaskMaxAttempts,
          instructions: newTaskInstructions.trim() || undefined,
        },
      });

      // Reset form
      setShowAddTaskForm(false);
      setNewTaskType(TaskType.QUIZ);
      setNewTaskParagraphId(null);
      setNewTaskChapterId(null);
      setNewTaskPoints(10);
      setNewTaskMaxAttempts(1);
      setNewTaskInstructions('');
    } catch {
      setFormError(t('errors.createFailed'));
    }
  };

  // Delete task
  const handleDeleteTask = async (taskId: number) => {
    setDeletingTaskId(taskId);
    try {
      await deleteTask.mutateAsync({ taskId, homeworkId });
    } catch {
      setFormError(t('errors.updateFailed'));
    } finally {
      setDeletingTaskId(null);
    }
  };

  // Generate questions
  const handleGenerateQuestions = async (taskId: number, params: GenerationParams) => {
    setGeneratingTaskId(taskId);
    try {
      await generateQuestions.mutateAsync({
        taskId,
        params,
        regenerate: true,
        homeworkId,
      });
    } catch (err: any) {
      // Show detailed error from API if available
      const apiError = err?.response?.data?.detail || err?.message;
      setFormError(apiError || t('errors.generateFailed'));
    } finally {
      setGeneratingTaskId(null);
    }
  };

  // Toggle task expansion
  const toggleTask = (taskId: number) => {
    setExpandedTasks((prev) => {
      const next = new Set(prev);
      if (next.has(taskId)) {
        next.delete(taskId);
      } else {
        next.add(taskId);
      }
      return next;
    });
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // Error state
  if (error || !homework) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <p className="text-destructive">{t('errors.loadFailed')}</p>
        <Link href={`/${locale}/homework`}>
          <Button variant="outline">{tCommon('back')}</Button>
        </Link>
      </div>
    );
  }

  // Not draft - should not happen due to redirect
  if (homework.status !== HomeworkStatus.DRAFT) {
    return null;
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href={`/${locale}/homework/${homeworkId}`}>
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{t('editTitle')}</h1>
            <HomeworkStatusBadge status={homework.status} />
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleSave}
            disabled={!isDirty || isSaving}
          >
            {isSaving ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Save className="h-4 w-4 mr-2" />
            )}
            {t('actions.saveChanges')}
          </Button>
          <Button
            variant="destructive"
            onClick={() => setShowDeleteDialog(true)}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            {t('actions.deleteDraft')}
          </Button>
          <Button
            onClick={handlePublish}
            disabled={homework.tasks.length === 0 || publishHomework.isPending}
          >
            {publishHomework.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Send className="h-4 w-4 mr-2" />
            )}
            {t('actions.publish')}
          </Button>
        </div>
      </div>

      {/* Error */}
      {formError && (
        <div className="bg-destructive/10 text-destructive p-3 rounded-md text-sm">
          {formError}
        </div>
      )}

      {/* Section 1: Basic Info */}
      <Card>
        <CardHeader>
          <CardTitle>{t('sections.basicInfo')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">{t('form.title')} *</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder={t('form.titlePlaceholder')}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">{t('form.description')}</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={t('form.descriptionPlaceholder')}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>{t('form.class')}</Label>
              <Select value={homework.class_id.toString()} disabled>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {classes?.map((c) => (
                    <SelectItem key={c.id} value={c.id.toString()}>
                      {c.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                {t('edit.classCannotChange')}
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="dueDate">{t('form.dueDate')} *</Label>
              <Input
                id="dueDate"
                type="datetime-local"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>{t('form.difficulty')}</Label>
            <Select
              value={targetDifficulty}
              onValueChange={(v) => setTargetDifficulty(v as any)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="auto">{t('form.difficultyAuto')}</SelectItem>
                <SelectItem value="easy">{t('form.difficultyEasy')}</SelectItem>
                <SelectItem value="medium">{t('form.difficultyMedium')}</SelectItem>
                <SelectItem value="hard">{t('form.difficultyHard')}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* AI Settings */}
          <div className="space-y-3 pt-4 border-t">
            <h3 className="font-medium flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              {t('ai.title')}
            </h3>
            <label className="flex items-center gap-3 cursor-pointer">
              <Checkbox
                checked={aiGenerationEnabled}
                onCheckedChange={(v) => setAiGenerationEnabled(!!v)}
              />
              <div>
                <p className="text-sm font-medium">{t('ai.generation')}</p>
                <p className="text-xs text-muted-foreground">{t('ai.generationDesc')}</p>
              </div>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <Checkbox
                checked={aiCheckEnabled}
                onCheckedChange={(v) => setAiCheckEnabled(!!v)}
              />
              <div>
                <p className="text-sm font-medium">{t('ai.checking')}</p>
                <p className="text-xs text-muted-foreground">{t('ai.checkingDesc')}</p>
              </div>
            </label>
          </div>
        </CardContent>
      </Card>

      {/* Section 2: Tasks */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>{t('sections.tasks')}</CardTitle>
            <Button
              size="sm"
              onClick={() => setShowAddTaskForm(!showAddTaskForm)}
            >
              <Plus className="h-4 w-4 mr-2" />
              {t('task.add')}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Add Task Form */}
          {showAddTaskForm && (
            <Card className="border-primary">
              <CardHeader className="pb-2">
                <CardTitle className="text-base">{t('task.add')}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>{t('task.type')}</Label>
                  <TaskTypeSelector
                    value={newTaskType}
                    onChange={setNewTaskType}
                  />
                </div>

                <ContentSelector
                  onSelect={(selection) => {
                    setNewTaskParagraphId(selection.paragraphId || null);
                    setNewTaskChapterId(selection.chapterId || null);
                  }}
                />

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>{t('task.points')}</Label>
                    <Input
                      type="number"
                      min={1}
                      max={100}
                      value={newTaskPoints}
                      onChange={(e) => setNewTaskPoints(Number(e.target.value))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>{t('task.maxAttempts')}</Label>
                    <Input
                      type="number"
                      min={1}
                      max={10}
                      value={newTaskMaxAttempts}
                      onChange={(e) => setNewTaskMaxAttempts(Number(e.target.value))}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>{t('task.instructions')}</Label>
                  <Textarea
                    value={newTaskInstructions}
                    onChange={(e) => setNewTaskInstructions(e.target.value)}
                    placeholder={t('task.instructionsPlaceholder')}
                  />
                </div>

                <div className="flex justify-end gap-2">
                  <Button
                    variant="outline"
                    onClick={() => setShowAddTaskForm(false)}
                  >
                    {tCommon('cancel')}
                  </Button>
                  <Button
                    onClick={handleAddTask}
                    disabled={addTask.isPending}
                  >
                    {addTask.isPending && (
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    )}
                    {t('task.add')}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Existing Tasks */}
          {homework.tasks.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              {t('task.noTasks')}
            </p>
          ) : (
            <div className="space-y-3">
              {homework.tasks.map((task, index) => (
                <Card key={task.id}>
                  <CardHeader
                    className="pb-2 cursor-pointer"
                    onClick={() => toggleTask(task.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {expandedTasks.has(task.id) ? (
                          <ChevronUp className="h-4 w-4 text-muted-foreground" />
                        ) : (
                          <ChevronDown className="h-4 w-4 text-muted-foreground" />
                        )}
                        <CardTitle className="text-base">
                          {index + 1}. {t(`task.types.${task.task_type}`)}
                        </CardTitle>
                        <span className="text-sm text-muted-foreground">
                          {task.paragraph_title || task.chapter_title}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-muted-foreground">
                          {task.points} {t('task.points')} | {task.questions_count || 0} {t('question.title').toLowerCase()}
                        </span>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteTask(task.id);
                          }}
                          disabled={deletingTaskId === task.id}
                        >
                          {deletingTaskId === task.id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Trash2 className="h-4 w-4 text-destructive" />
                          )}
                        </Button>
                      </div>
                    </div>
                  </CardHeader>

                  {expandedTasks.has(task.id) && (
                    <CardContent className="space-y-4">
                      {task.instructions && (
                        <p className="text-sm text-muted-foreground">
                          {task.instructions}
                        </p>
                      )}

                      {/* AI Generation Panel */}
                      {aiGenerationEnabled && (
                        <AIGenerationPanel
                          onGenerate={(params) => handleGenerateQuestions(task.id, params)}
                          isGenerating={generatingTaskId === task.id}
                          hasQuestions={(task.questions?.length || 0) > 0}
                        />
                      )}

                      {/* Questions */}
                      {task.questions && task.questions.length > 0 && (
                        <div className="space-y-3">
                          <h4 className="font-medium">
                            {t('question.title')} ({task.questions.length})
                          </h4>
                          {task.questions.map((q, qi) => (
                            <QuestionCard
                              key={q.id}
                              question={q}
                              index={qi}
                              showAnswer
                            />
                          ))}
                        </div>
                      )}
                    </CardContent>
                  )}
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('actions.deleteDraft')}</DialogTitle>
            <DialogDescription>
              {t('actions.confirmDeleteDraft')}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDeleteDialog(false)}
            >
              {tCommon('cancel')}
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteHomework.isPending}
            >
              {deleteHomework.isPending && (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              )}
              {tCommon('delete')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
