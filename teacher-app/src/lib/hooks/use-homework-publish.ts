/**
 * Hook for homework creation + publish flow.
 * Orchestrates: create draft → add tasks → generate questions → publish.
 */
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useLocale } from 'next-intl';
import {
  useCreateHomework,
  useAddTask,
  useGenerateQuestions,
  usePublishHomework,
} from '@/lib/hooks/use-homework';
import type { QuickTaskDraft } from '@/components/homework/QuickTaskCard';
import type { TemplateTaskDef } from '@/components/homework/HomeworkTemplates';
import type { GenerationParams, BloomLevel } from '@/types/homework';

export type PublishStep = 'idle' | 'creating' | 'tasks' | 'generating' | 'publishing' | 'done';

interface HomeworkFormData {
  title: string;
  classId: number;
  dueDate: string;
  targetDifficulty: string;
  aiGenerationEnabled: boolean;
  aiCheckEnabled: boolean;
  bloomLevels: BloomLevel[];
}

interface UseHomeworkPublishReturn {
  publishStep: PublishStep;
  isSubmitting: boolean;
  error: string | null;
  setError: (error: string | null) => void;
  handlePublish: (
    formData: HomeworkFormData,
    tasks: QuickTaskDraft[],
    templateDefs: Map<string, TemplateTaskDef>,
    errorMessages: { createFailed: string; draftFallback: string },
  ) => Promise<void>;
  handleSaveDraft: (
    formData: HomeworkFormData,
    tasks: QuickTaskDraft[],
    errorMessages: { createFailed: string },
  ) => Promise<void>;
}

export function useHomeworkPublish(): UseHomeworkPublishReturn {
  const router = useRouter();
  const locale = useLocale();

  const [publishStep, setPublishStep] = useState<PublishStep>('idle');
  const [error, setError] = useState<string | null>(null);

  const createHomework = useCreateHomework();
  const addTask = useAddTask();
  const generateQuestions = useGenerateQuestions();
  const publishHomework = usePublishHomework();

  const createDraftAndTasks = async (
    formData: HomeworkFormData,
    tasks: QuickTaskDraft[],
  ) => {
    // Step 1: Create homework draft
    setPublishStep('creating');
    const homework = await createHomework.mutateAsync({
      title: formData.title.trim(),
      class_id: formData.classId,
      due_date: new Date(formData.dueDate).toISOString(),
      target_difficulty: formData.targetDifficulty as 'easy' | 'medium' | 'hard' | 'auto',
      ai_generation_enabled: formData.aiGenerationEnabled,
      ai_check_enabled: formData.aiCheckEnabled,
    });

    // Step 2: Add tasks
    setPublishStep('tasks');
    const taskIds: { clientId: string; serverId: number }[] = [];
    for (const task of tasks) {
      const result = await addTask.mutateAsync({
        homeworkId: homework.id,
        data: {
          paragraph_id: task.paragraphId,
          chapter_id: task.chapterId,
          task_type: task.taskType,
          points: task.points,
          max_attempts: task.maxAttempts,
        },
      });
      taskIds.push({ clientId: task.id, serverId: result.id });
    }

    return { homework, taskIds };
  };

  const handlePublish = async (
    formData: HomeworkFormData,
    tasks: QuickTaskDraft[],
    templateDefs: Map<string, TemplateTaskDef>,
    errorMessages: { createFailed: string; draftFallback: string },
  ) => {
    setError(null);

    try {
      const { homework, taskIds } = await createDraftAndTasks(formData, tasks);

      // Step 3: Generate questions (if AI enabled)
      if (formData.aiGenerationEnabled) {
        setPublishStep('generating');
        for (const { clientId, serverId } of taskIds) {
          const def = templateDefs.get(clientId);
          const baseParams = def?.generationParams || {
            questions_count: 5,
            include_explanation: true,
          };
          const params: GenerationParams = {
            ...baseParams,
            bloom_levels: formData.bloomLevels.length > 0 ? formData.bloomLevels : baseParams.bloom_levels,
          };
          try {
            await generateQuestions.mutateAsync({
              taskId: serverId,
              params,
              homeworkId: homework.id,
            });
          } catch {
            setPublishStep('idle');
            setError(errorMessages.draftFallback);
            router.push(`/${locale}/homework/${homework.id}/edit`);
            return;
          }
        }
      }

      // Step 4: Publish
      setPublishStep('publishing');
      await publishHomework.mutateAsync({ homeworkId: homework.id });

      setPublishStep('done');
      router.push(`/${locale}/homework`);
    } catch (err: any) {
      setPublishStep('idle');
      const apiError = err?.response?.data?.detail || err?.message;
      setError(apiError || errorMessages.createFailed);
    }
  };

  const handleSaveDraft = async (
    formData: HomeworkFormData,
    tasks: QuickTaskDraft[],
    errorMessages: { createFailed: string },
  ) => {
    setError(null);

    try {
      const { homework } = await createDraftAndTasks(formData, tasks);
      router.push(`/${locale}/homework/${homework.id}/edit`);
    } catch (err: any) {
      setPublishStep('idle');
      const apiError = err?.response?.data?.detail || err?.message;
      setError(apiError || errorMessages.createFailed);
    }
  };

  return {
    publishStep,
    isSubmitting: publishStep !== 'idle',
    error,
    setError,
    handlePublish,
    handleSaveDraft,
  };
}
