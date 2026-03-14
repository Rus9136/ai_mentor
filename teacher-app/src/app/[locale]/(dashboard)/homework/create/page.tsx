'use client';

import { useState, useCallback } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import Link from 'next/link';
import { ArrowLeft, Loader2, Plus, Check, ChevronDown, ChevronUp, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { HomeworkTemplates, HOMEWORK_TEMPLATES } from '@/components/homework/HomeworkTemplates';
import { QuickTaskCard } from '@/components/homework/QuickTaskCard';
import type { QuickTaskDraft } from '@/components/homework/QuickTaskCard';
import type { HomeworkTemplate, TemplateTaskDef } from '@/components/homework/HomeworkTemplates';
import { useClasses } from '@/lib/hooks/use-teacher-data';
import { useHomeworkPublish } from '@/lib/hooks/use-homework-publish';
import type { PublishStep } from '@/lib/hooks/use-homework-publish';
import { TaskType } from '@/types/homework';

export default function CreateHomeworkPage() {
  const locale = useLocale();
  const t = useTranslations('homework');

  // Template
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [templateDefs, setTemplateDefs] = useState<Map<string, TemplateTaskDef>>(new Map());

  // Form fields
  const [title, setTitle] = useState('');
  const [titleManuallyEdited, setTitleManuallyEdited] = useState(false);
  const [classId, setClassId] = useState<number | null>(null);
  const [dueDate, setDueDate] = useState('');
  const [tasks, setTasks] = useState<QuickTaskDraft[]>([]);

  // Advanced settings
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [targetDifficulty, setTargetDifficulty] = useState('auto');
  const [aiGenerationEnabled, setAiGenerationEnabled] = useState(true);
  const [aiCheckEnabled, setAiCheckEnabled] = useState(true);

  // Hooks
  const { data: classes } = useClasses();
  const { publishStep, isSubmitting, error, setError, handlePublish, handleSaveDraft } = useHomeworkPublish();

  // Template selection
  const handleTemplateSelect = useCallback((template: HomeworkTemplate) => {
    setSelectedTemplate(template.id);

    if (template.id === 'custom') {
      setTasks([]);
      setTemplateDefs(new Map());
      return;
    }

    const newDefs = new Map<string, TemplateTaskDef>();
    const newTasks = template.tasks.map((def) => {
      const task: QuickTaskDraft = {
        id: crypto.randomUUID(),
        taskType: def.taskType,
        paragraph: null,
        points: def.points,
        maxAttempts: def.maxAttempts,
      };
      newDefs.set(task.id, def);
      return task;
    });

    setTasks(newTasks);
    setTemplateDefs(newDefs);

    if (!titleManuallyEdited) {
      setTitle(t(`templates.${template.labelKey}`));
    }
  }, [t, titleManuallyEdited]);

  // Task CRUD
  const handleTaskChange = useCallback((id: string, updates: Partial<QuickTaskDraft>) => {
    setTasks((prev) => prev.map((task) => {
      if (task.id !== id) return task;
      const updated = { ...task, ...updates };

      // Auto-title from first task's paragraph
      if (updates.paragraph && prev.indexOf(task) === 0 && !titleManuallyEdited) {
        const p = updates.paragraph;
        const tplName = selectedTemplate && selectedTemplate !== 'custom'
          ? HOMEWORK_TEMPLATES.find((tpl) => tpl.id === selectedTemplate)?.labelKey
          : null;
        const prefix = tplName ? t(`templates.${tplName}`) : '';
        setTitle(`${prefix} — §${p.number}. ${p.title || ''}`.trim());
      }

      return updated;
    }));
  }, [titleManuallyEdited, selectedTemplate, t]);

  const handleTaskDelete = useCallback((id: string) => {
    setTasks((prev) => prev.filter((task) => task.id !== id));
    setTemplateDefs((prev) => {
      const next = new Map(prev);
      next.delete(id);
      return next;
    });
  }, []);

  const handleAddTask = useCallback(() => {
    setTasks((prev) => [...prev, {
      id: crypto.randomUUID(),
      taskType: TaskType.QUIZ,
      paragraph: null,
      points: 10,
      maxAttempts: 3,
    }]);
  }, []);

  // Validation
  const validate = (): string | null => {
    if (!title.trim()) return t('errors.noTitle');
    if (!classId) return t('errors.noClass');
    if (!dueDate) return t('errors.noDueDate');
    if (tasks.length === 0) return t('errors.noTasks');
    const tasksWithoutParagraph = tasks.some((task) => !task.paragraph);
    if (tasksWithoutParagraph) return t('errors.noParagraph');
    return null;
  };

  const hasAllParagraphs = tasks.length > 0 && tasks.every((task) => task.paragraph);

  const formData = {
    title, classId: classId!, dueDate, targetDifficulty, aiGenerationEnabled, aiCheckEnabled,
  };

  const onPublish = async () => {
    const err = validate();
    if (err) { setError(err); return; }
    await handlePublish(formData, tasks, templateDefs, {
      createFailed: t('errors.createFailed'),
      draftFallback: t('publishProgress.draftFallback'),
    });
  };

  const onSaveDraft = async () => {
    const err = validate();
    if (err) { setError(err); return; }
    await handleSaveDraft(formData, tasks, { createFailed: t('errors.createFailed') });
  };

  const publishStepLabels: Record<PublishStep, string> = {
    idle: '', creating: t('publishProgress.creating'),
    tasks: t('publishProgress.addingTasks'), generating: t('publishProgress.generating'),
    publishing: t('publishProgress.publishing'), done: '',
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href={`/${locale}/homework`}>
          <Button variant="ghost" size="icon"><ArrowLeft className="h-4 w-4" /></Button>
        </Link>
        <h1 className="text-2xl font-bold">{t('create')}</h1>
      </div>

      {/* Templates */}
      <HomeworkTemplates selected={selectedTemplate} onSelect={handleTemplateSelect} />

      {/* Error */}
      {error && (
        <div className="bg-destructive/10 text-destructive p-3 rounded-md text-sm">{error}</div>
      )}

      {/* Form */}
      <Card>
        <CardContent className="pt-6 space-y-5">
          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="title">{t('form.title')} *</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => { setTitle(e.target.value); setTitleManuallyEdited(true); }}
              placeholder={t('form.titlePlaceholder')}
              disabled={isSubmitting}
            />
          </div>

          {/* Class + Due Date */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>{t('form.class')} *</Label>
              <Select
                value={classId?.toString() || ''}
                onValueChange={(v) => setClassId(Number(v))}
                disabled={isSubmitting}
              >
                <SelectTrigger>
                  <SelectValue placeholder={t('form.selectClass')} />
                </SelectTrigger>
                <SelectContent>
                  {classes?.map((c) => (
                    <SelectItem key={c.id} value={c.id.toString()}>{c.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="dueDate">{t('form.dueDate')} *</Label>
              <Input
                id="dueDate"
                type="datetime-local"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                disabled={isSubmitting}
              />
            </div>
          </div>

          {/* Tasks */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label>{t('task.title')}</Label>
              <Button type="button" variant="outline" size="sm" onClick={handleAddTask} disabled={isSubmitting}>
                <Plus className="h-3.5 w-3.5 mr-1.5" />{t('task.add')}
              </Button>
            </div>

            {tasks.length === 0 ? (
              <div className="text-center text-muted-foreground py-6 border border-dashed rounded-lg">
                <p>{t('task.noTasks')}</p>
                <p className="text-xs mt-1">{t('task.addFirst')}</p>
              </div>
            ) : (
              <div className="space-y-3">
                {tasks.map((task, i) => (
                  <QuickTaskCard
                    key={task.id} task={task} index={i}
                    onChange={handleTaskChange} onDelete={handleTaskDelete} disabled={isSubmitting}
                  />
                ))}
              </div>
            )}

            {/* AI generation info */}
            {hasAllParagraphs && aiGenerationEnabled && (
              <div className="flex items-start gap-2 rounded-lg bg-primary/5 border border-primary/20 p-3">
                <Sparkles className="h-4 w-4 text-primary mt-0.5 shrink-0" />
                <p className="text-sm text-muted-foreground">
                  {t('publishProgress.aiHint')}
                </p>
              </div>
            )}
          </div>

          {/* Advanced Settings */}
          <div className="border-t pt-4">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors w-full"
            >
              {showAdvanced ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              {t('advancedSettings')}
            </button>

            {showAdvanced && (
              <div className="mt-4 space-y-4">
                <div className="space-y-2">
                  <Label>{t('form.difficulty')}</Label>
                  <Select value={targetDifficulty} onValueChange={setTargetDifficulty} disabled={isSubmitting}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="auto">{t('form.difficultyAuto')}</SelectItem>
                      <SelectItem value="easy">{t('form.difficultyEasy')}</SelectItem>
                      <SelectItem value="medium">{t('form.difficultyMedium')}</SelectItem>
                      <SelectItem value="hard">{t('form.difficultyHard')}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-3">
                  <h4 className="font-medium flex items-center gap-2 text-sm">
                    <Sparkles className="h-4 w-4 text-primary" />{t('ai.title')}
                  </h4>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <Checkbox checked={aiGenerationEnabled} onCheckedChange={(v) => setAiGenerationEnabled(v as boolean)} disabled={isSubmitting} />
                    <div>
                      <p className="text-sm font-medium">{t('ai.generation')}</p>
                      <p className="text-xs text-muted-foreground">{t('ai.generationDesc')}</p>
                    </div>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <Checkbox checked={aiCheckEnabled} onCheckedChange={(v) => setAiCheckEnabled(v as boolean)} disabled={isSubmitting} />
                    <div>
                      <p className="text-sm font-medium">{t('ai.checking')}</p>
                      <p className="text-xs text-muted-foreground">{t('ai.checkingDesc')}</p>
                    </div>
                  </label>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex justify-end gap-3">
        <Button variant="outline" onClick={onSaveDraft} disabled={isSubmitting}>
          {t('actions.saveDraft')}
        </Button>
        <Button onClick={onPublish} disabled={isSubmitting}>
          {isSubmitting ? (
            <><Loader2 className="h-4 w-4 animate-spin mr-2" />{publishStepLabels[publishStep]}</>
          ) : aiGenerationEnabled ? (
            <><Sparkles className="h-4 w-4 mr-2" />{t('actions.generateAndPublish')}</>
          ) : (
            <><Check className="h-4 w-4 mr-2" />{t('actions.publish')}</>
          )}
        </Button>
      </div>
    </div>
  );
}
