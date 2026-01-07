'use client';

import { useState, useReducer } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations, useLocale } from 'next-intl';
import Link from 'next/link';
import {
  ArrowLeft,
  ArrowRight,
  Loader2,
  Plus,
  Trash2,
  Sparkles,
  Check,
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
  TaskTypeSelector,
  ContentSelector,
  AIGenerationPanel,
  QuestionCard,
} from '@/components/homework';
import { useClasses } from '@/lib/hooks/use-teacher-data';
import {
  useCreateHomework,
  useAddTask,
  useGenerateQuestions,
  usePublishHomework,
} from '@/lib/hooks/use-homework';
import { TaskType, HomeworkStatus, type HomeworkTaskCreate, type GenerationParams } from '@/types/homework';

// Wizard State
interface WizardState {
  step: number;
  // Step 1: Basic Info
  title: string;
  description: string;
  classId: number | null;
  dueDate: string;
  targetDifficulty: 'easy' | 'medium' | 'hard' | 'auto';
  aiGenerationEnabled: boolean;
  aiCheckEnabled: boolean;
  // Step 2: Tasks
  tasks: TaskDraft[];
  // Created homework ID
  homeworkId: number | null;
}

interface TaskDraft {
  id: string;
  paragraphId?: number;
  chapterId?: number;
  taskType: TaskType;
  points: number;
  maxAttempts: number;
  instructions: string;
  paragraphTitle?: string;
  // Server-created task ID
  serverId?: number;
  // Questions
  questions: any[];
  isGenerating?: boolean;
}

type WizardAction =
  | { type: 'SET_FIELD'; field: keyof WizardState; value: any }
  | { type: 'NEXT_STEP' }
  | { type: 'PREV_STEP' }
  | { type: 'ADD_TASK'; task: TaskDraft }
  | { type: 'REMOVE_TASK'; id: string }
  | { type: 'UPDATE_TASK'; id: string; updates: Partial<TaskDraft> }
  | { type: 'SET_HOMEWORK_ID'; id: number }
  | { type: 'SET_TASK_SERVER_ID'; taskId: string; serverId: number }
  | { type: 'SET_TASK_QUESTIONS'; taskId: string; questions: any[] }
  | { type: 'SET_TASK_GENERATING'; taskId: string; isGenerating: boolean };

function wizardReducer(state: WizardState, action: WizardAction): WizardState {
  switch (action.type) {
    case 'SET_FIELD':
      return { ...state, [action.field]: action.value };
    case 'NEXT_STEP':
      return { ...state, step: Math.min(state.step + 1, 4) };
    case 'PREV_STEP':
      return { ...state, step: Math.max(state.step - 1, 1) };
    case 'ADD_TASK':
      return { ...state, tasks: [...state.tasks, action.task] };
    case 'REMOVE_TASK':
      return { ...state, tasks: state.tasks.filter((t) => t.id !== action.id) };
    case 'UPDATE_TASK':
      return {
        ...state,
        tasks: state.tasks.map((t) =>
          t.id === action.id ? { ...t, ...action.updates } : t
        ),
      };
    case 'SET_HOMEWORK_ID':
      return { ...state, homeworkId: action.id };
    case 'SET_TASK_SERVER_ID':
      return {
        ...state,
        tasks: state.tasks.map((t) =>
          t.id === action.taskId ? { ...t, serverId: action.serverId } : t
        ),
      };
    case 'SET_TASK_QUESTIONS':
      return {
        ...state,
        tasks: state.tasks.map((t) =>
          t.id === action.taskId ? { ...t, questions: action.questions } : t
        ),
      };
    case 'SET_TASK_GENERATING':
      return {
        ...state,
        tasks: state.tasks.map((t) =>
          t.id === action.taskId ? { ...t, isGenerating: action.isGenerating } : t
        ),
      };
    default:
      return state;
  }
}

const initialState: WizardState = {
  step: 1,
  title: '',
  description: '',
  classId: null,
  dueDate: '',
  targetDifficulty: 'auto',
  aiGenerationEnabled: true,
  aiCheckEnabled: true,
  tasks: [],
  homeworkId: null,
};

export default function CreateHomeworkPage() {
  const router = useRouter();
  const locale = useLocale();
  const t = useTranslations('homework');

  const [state, dispatch] = useReducer(wizardReducer, initialState);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { data: classes } = useClasses();
  const createHomework = useCreateHomework();
  const addTask = useAddTask();
  const generateQuestions = useGenerateQuestions();
  const publishHomework = usePublishHomework();

  // Step 1: Create homework draft
  const handleCreateDraft = async () => {
    if (!state.title || !state.classId || !state.dueDate) {
      setError(t('errors.noTitle'));
      return;
    }

    setIsCreating(true);
    setError(null);

    try {
      const result = await createHomework.mutateAsync({
        title: state.title,
        description: state.description || undefined,
        class_id: state.classId,
        due_date: new Date(state.dueDate).toISOString(),
        target_difficulty: state.targetDifficulty,
        ai_generation_enabled: state.aiGenerationEnabled,
        ai_check_enabled: state.aiCheckEnabled,
      });

      dispatch({ type: 'SET_HOMEWORK_ID', id: result.id });
      dispatch({ type: 'NEXT_STEP' });
    } catch (err: any) {
      const apiError = err?.response?.data?.detail || err?.message;
      setError(apiError || t('errors.createFailed'));
    } finally {
      setIsCreating(false);
    }
  };

  // Step 2: Add task
  const handleAddTask = () => {
    const newTask: TaskDraft = {
      id: crypto.randomUUID(),
      taskType: TaskType.QUIZ,
      points: 10,
      maxAttempts: 1,
      instructions: '',
      questions: [],
    };
    dispatch({ type: 'ADD_TASK', task: newTask });
  };

  // Step 2: Save tasks to server
  const handleSaveTasks = async () => {
    if (!state.homeworkId) return;

    setIsCreating(true);
    setError(null);

    try {
      for (const task of state.tasks) {
        if (!task.serverId && (task.paragraphId || task.chapterId)) {
          const result = await addTask.mutateAsync({
            homeworkId: state.homeworkId,
            data: {
              paragraph_id: task.paragraphId,
              chapter_id: task.chapterId,
              task_type: task.taskType,
              points: task.points,
              max_attempts: task.maxAttempts,
              instructions: task.instructions || undefined,
            },
          });
          dispatch({ type: 'SET_TASK_SERVER_ID', taskId: task.id, serverId: result.id });
        }
      }
      dispatch({ type: 'NEXT_STEP' });
    } catch (err: any) {
      const apiError = err?.response?.data?.detail || err?.message;
      setError(apiError || t('errors.createFailed'));
    } finally {
      setIsCreating(false);
    }
  };

  // Step 3: Generate questions
  const handleGenerateQuestions = async (taskId: string, params: GenerationParams) => {
    const task = state.tasks.find((t) => t.id === taskId);
    if (!task?.serverId || !state.homeworkId) return;

    dispatch({ type: 'SET_TASK_GENERATING', taskId, isGenerating: true });

    try {
      const questions = await generateQuestions.mutateAsync({
        taskId: task.serverId,
        params,
        homeworkId: state.homeworkId,
      });
      dispatch({ type: 'SET_TASK_QUESTIONS', taskId, questions });
    } catch (err: any) {
      // Show detailed error from API if available
      const apiError = err?.response?.data?.detail || err?.message;
      setError(apiError || t('errors.generateFailed'));
    } finally {
      dispatch({ type: 'SET_TASK_GENERATING', taskId, isGenerating: false });
    }
  };

  // Step 4: Publish
  const handlePublish = async () => {
    if (!state.homeworkId) return;

    setIsCreating(true);
    try {
      await publishHomework.mutateAsync({ homeworkId: state.homeworkId });
      router.push(`/${locale}/homework`);
    } catch (err: any) {
      const apiError = err?.response?.data?.detail || err?.message;
      setError(apiError || t('errors.publishFailed'));
    } finally {
      setIsCreating(false);
    }
  };

  // Save as draft and exit
  const handleSaveDraft = () => {
    router.push(`/${locale}/homework`);
  };

  const steps = [
    { num: 1, label: t('wizard.step1') },
    { num: 2, label: t('wizard.step2') },
    { num: 3, label: t('wizard.step3') },
    { num: 4, label: t('wizard.step4') },
  ];

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href={`/${locale}/homework`}>
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <h1 className="text-2xl font-bold">{t('create')}</h1>
      </div>

      {/* Steps Indicator */}
      <div className="flex items-center justify-center gap-2">
        {steps.map((s, i) => (
          <div key={s.num} className="flex items-center">
            <div
              className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${
                state.step >= s.num
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground'
              }`}
            >
              {state.step > s.num ? <Check className="h-4 w-4" /> : s.num}
            </div>
            <span className="ml-2 text-sm hidden sm:inline">{s.label}</span>
            {i < steps.length - 1 && (
              <div className="w-8 h-px bg-muted mx-2" />
            )}
          </div>
        ))}
      </div>

      {/* Error */}
      {error && (
        <div className="bg-destructive/10 text-destructive p-3 rounded-md text-sm">
          {error}
        </div>
      )}

      {/* Step 1: Basic Info */}
      {state.step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle>{t('wizard.step1')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="title">{t('form.title')} *</Label>
              <Input
                id="title"
                value={state.title}
                onChange={(e) =>
                  dispatch({ type: 'SET_FIELD', field: 'title', value: e.target.value })
                }
                placeholder={t('form.titlePlaceholder')}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">{t('form.description')}</Label>
              <Textarea
                id="description"
                value={state.description}
                onChange={(e) =>
                  dispatch({ type: 'SET_FIELD', field: 'description', value: e.target.value })
                }
                placeholder={t('form.descriptionPlaceholder')}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>{t('form.class')} *</Label>
                <Select
                  value={state.classId?.toString() || ''}
                  onValueChange={(v) =>
                    dispatch({ type: 'SET_FIELD', field: 'classId', value: Number(v) })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder={t('form.selectClass')} />
                  </SelectTrigger>
                  <SelectContent>
                    {classes?.map((c) => (
                      <SelectItem key={c.id} value={c.id.toString()}>
                        {c.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="dueDate">{t('form.dueDate')} *</Label>
                <Input
                  id="dueDate"
                  type="datetime-local"
                  value={state.dueDate}
                  onChange={(e) =>
                    dispatch({ type: 'SET_FIELD', field: 'dueDate', value: e.target.value })
                  }
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>{t('form.difficulty')}</Label>
              <Select
                value={state.targetDifficulty}
                onValueChange={(v) =>
                  dispatch({ type: 'SET_FIELD', field: 'targetDifficulty', value: v })
                }
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
                  checked={state.aiGenerationEnabled}
                  onCheckedChange={(v) =>
                    dispatch({ type: 'SET_FIELD', field: 'aiGenerationEnabled', value: v })
                  }
                />
                <div>
                  <p className="text-sm font-medium">{t('ai.generation')}</p>
                  <p className="text-xs text-muted-foreground">{t('ai.generationDesc')}</p>
                </div>
              </label>
              <label className="flex items-center gap-3 cursor-pointer">
                <Checkbox
                  checked={state.aiCheckEnabled}
                  onCheckedChange={(v) =>
                    dispatch({ type: 'SET_FIELD', field: 'aiCheckEnabled', value: v })
                  }
                />
                <div>
                  <p className="text-sm font-medium">{t('ai.checking')}</p>
                  <p className="text-xs text-muted-foreground">{t('ai.checkingDesc')}</p>
                </div>
              </label>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Tasks */}
      {state.step === 2 && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>{t('wizard.step2')}</CardTitle>
                <Button onClick={handleAddTask} size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  {t('task.add')}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {state.tasks.length === 0 ? (
                <p className="text-center text-muted-foreground py-8">
                  {t('task.noTasks')}
                </p>
              ) : (
                <div className="space-y-4">
                  {state.tasks.map((task, i) => (
                    <Card key={task.id}>
                      <CardHeader className="pb-2">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-base">
                            {t('task.title')} #{i + 1}
                          </CardTitle>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() =>
                              dispatch({ type: 'REMOVE_TASK', id: task.id })
                            }
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="space-y-2">
                          <Label>{t('task.type')}</Label>
                          <TaskTypeSelector
                            value={task.taskType}
                            onChange={(v) =>
                              dispatch({
                                type: 'UPDATE_TASK',
                                id: task.id,
                                updates: { taskType: v },
                              })
                            }
                          />
                        </div>

                        <ContentSelector
                          onSelect={(selection) =>
                            dispatch({
                              type: 'UPDATE_TASK',
                              id: task.id,
                              updates: {
                                paragraphId: selection.paragraphId,
                                chapterId: selection.chapterId,
                              },
                            })
                          }
                        />

                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>{t('task.points')}</Label>
                            <Input
                              type="number"
                              min={1}
                              max={100}
                              value={task.points}
                              onChange={(e) =>
                                dispatch({
                                  type: 'UPDATE_TASK',
                                  id: task.id,
                                  updates: { points: Number(e.target.value) },
                                })
                              }
                            />
                          </div>
                          <div className="space-y-2">
                            <Label>{t('task.maxAttempts')}</Label>
                            <Input
                              type="number"
                              min={1}
                              max={10}
                              value={task.maxAttempts}
                              onChange={(e) =>
                                dispatch({
                                  type: 'UPDATE_TASK',
                                  id: task.id,
                                  updates: { maxAttempts: Number(e.target.value) },
                                })
                              }
                            />
                          </div>
                        </div>

                        <div className="space-y-2">
                          <Label>{t('task.instructions')}</Label>
                          <Textarea
                            value={task.instructions}
                            onChange={(e) =>
                              dispatch({
                                type: 'UPDATE_TASK',
                                id: task.id,
                                updates: { instructions: e.target.value },
                              })
                            }
                            placeholder={t('task.instructionsPlaceholder')}
                          />
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Step 3: Questions */}
      {state.step === 3 && (
        <div className="space-y-4">
          {state.tasks.map((task, i) => (
            <Card key={task.id}>
              <CardHeader>
                <CardTitle className="text-base">
                  {t('task.title')} #{i + 1}: {task.paragraphTitle || t(`task.types.${task.taskType}`)}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {state.aiGenerationEnabled && (
                  <AIGenerationPanel
                    onGenerate={(params) => handleGenerateQuestions(task.id, params)}
                    isGenerating={task.isGenerating}
                    hasQuestions={task.questions.length > 0}
                  />
                )}

                {task.questions.length > 0 && (
                  <div className="space-y-3">
                    <h4 className="font-medium">{t('question.title')} ({task.questions.length})</h4>
                    {task.questions.map((q, qi) => (
                      <QuestionCard key={q.id} question={q} index={qi} showAnswer />
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Step 4: Preview */}
      {state.step === 4 && (
        <Card>
          <CardHeader>
            <CardTitle>{t('wizard.step4')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">{t('form.title')}</p>
                <p className="font-medium">{state.title}</p>
              </div>
              <div>
                <p className="text-muted-foreground">{t('form.class')}</p>
                <p className="font-medium">
                  {classes?.find((c) => c.id === state.classId)?.name || '—'}
                </p>
              </div>
              <div>
                <p className="text-muted-foreground">{t('form.dueDate')}</p>
                <p className="font-medium">
                  {state.dueDate
                    ? new Date(state.dueDate).toLocaleString()
                    : '—'}
                </p>
              </div>
              <div>
                <p className="text-muted-foreground">{t('task.title')}</p>
                <p className="font-medium">{state.tasks.length}</p>
              </div>
            </div>

            <div className="pt-4 border-t">
              <p className="text-muted-foreground mb-2">{t('question.title')}</p>
              <p className="font-medium">
                {state.tasks.reduce((acc, t) => acc + t.questions.length, 0)} вопросов
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Navigation Buttons */}
      <div className="flex justify-between">
        <div>
          {state.step > 1 && (
            <Button
              variant="outline"
              onClick={() => dispatch({ type: 'PREV_STEP' })}
              disabled={isCreating}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              {t('actions.back')}
            </Button>
          )}
        </div>

        <div className="flex gap-2">
          {state.homeworkId && (
            <Button variant="outline" onClick={handleSaveDraft}>
              {t('actions.saveDraft')}
            </Button>
          )}

          {state.step === 1 && (
            <Button onClick={handleCreateDraft} disabled={isCreating}>
              {isCreating ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <ArrowRight className="h-4 w-4 mr-2" />
              )}
              {t('actions.next')}
            </Button>
          )}

          {state.step === 2 && (
            <Button
              onClick={handleSaveTasks}
              disabled={isCreating || state.tasks.length === 0}
            >
              {isCreating ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <ArrowRight className="h-4 w-4 mr-2" />
              )}
              {t('actions.next')}
            </Button>
          )}

          {state.step === 3 && (
            <Button onClick={() => dispatch({ type: 'NEXT_STEP' })}>
              <ArrowRight className="h-4 w-4 mr-2" />
              {t('actions.next')}
            </Button>
          )}

          {state.step === 4 && (
            <Button onClick={handlePublish} disabled={isCreating}>
              {isCreating ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <Check className="h-4 w-4 mr-2" />
              )}
              {t('actions.publish')}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
