'use client';

import { useTranslations } from 'next-intl';
import { BookOpen, Sparkles, Edit3, Briefcase, Library, Settings } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { TaskType, QuestionType, BloomLevel } from '@/types/homework';
import type { GenerationParams } from '@/types/homework';

export interface TemplateTaskDef {
  taskType: TaskType;
  points: number;
  maxAttempts: number;
  generationParams: GenerationParams;
}

export interface HomeworkTemplate {
  id: string;
  icon: typeof BookOpen;
  labelKey: string;
  descriptionKey: string;
  tasks: TemplateTaskDef[];
}

export const HOMEWORK_TEMPLATES: HomeworkTemplate[] = [
  {
    id: 'read_and_answer',
    icon: BookOpen,
    labelKey: 'readAndAnswer',
    descriptionKey: 'readAndAnswerDesc',
    tasks: [{
      taskType: TaskType.READ, points: 10, maxAttempts: 1,
      generationParams: { questions_count: 5, question_types: [QuestionType.SINGLE_CHOICE, QuestionType.TRUE_FALSE], bloom_levels: [BloomLevel.REMEMBER, BloomLevel.UNDERSTAND], include_explanation: true },
    }],
  },
  {
    id: 'quiz',
    icon: Sparkles,
    labelKey: 'quiz',
    descriptionKey: 'quizDesc',
    tasks: [{
      taskType: TaskType.QUIZ, points: 20, maxAttempts: 3,
      generationParams: { questions_count: 10, question_types: [QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE], bloom_levels: [BloomLevel.UNDERSTAND, BloomLevel.APPLY], include_explanation: true },
    }],
  },
  {
    id: 'essay',
    icon: Edit3,
    labelKey: 'essay',
    descriptionKey: 'essayDesc',
    tasks: [{
      taskType: TaskType.ESSAY, points: 30, maxAttempts: 1,
      generationParams: { questions_count: 1, question_types: [QuestionType.OPEN_ENDED], bloom_levels: [BloomLevel.ANALYZE, BloomLevel.EVALUATE, BloomLevel.CREATE], include_explanation: true },
    }],
  },
  {
    id: 'practice',
    icon: Briefcase,
    labelKey: 'practice',
    descriptionKey: 'practiceDesc',
    tasks: [{
      taskType: TaskType.PRACTICE, points: 20, maxAttempts: 3,
      generationParams: { questions_count: 3, question_types: [QuestionType.OPEN_ENDED], bloom_levels: [BloomLevel.APPLY, BloomLevel.ANALYZE], include_explanation: true },
    }],
  },
  {
    id: 'combined',
    icon: Library,
    labelKey: 'combined',
    descriptionKey: 'combinedDesc',
    tasks: [
      { taskType: TaskType.READ, points: 5, maxAttempts: 1, generationParams: { questions_count: 3, question_types: [QuestionType.SINGLE_CHOICE, QuestionType.TRUE_FALSE], bloom_levels: [BloomLevel.REMEMBER, BloomLevel.UNDERSTAND], include_explanation: true } },
      { taskType: TaskType.QUIZ, points: 15, maxAttempts: 3, generationParams: { questions_count: 5, question_types: [QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE], bloom_levels: [BloomLevel.UNDERSTAND, BloomLevel.APPLY], include_explanation: true } },
      { taskType: TaskType.OPEN_QUESTION, points: 10, maxAttempts: 2, generationParams: { questions_count: 2, question_types: [QuestionType.OPEN_ENDED], bloom_levels: [BloomLevel.ANALYZE, BloomLevel.EVALUATE], include_explanation: true } },
    ],
  },
  {
    id: 'custom',
    icon: Settings,
    labelKey: 'custom',
    descriptionKey: 'customDesc',
    tasks: [],
  },
];

interface HomeworkTemplatesProps {
  selected: string | null;
  onSelect: (template: HomeworkTemplate) => void;
}

export function HomeworkTemplates({ selected, onSelect }: HomeworkTemplatesProps) {
  const t = useTranslations('homework.templates');

  return (
    <div>
      <h3 className="text-sm font-medium text-muted-foreground mb-3">{t('title')}</h3>
      <div className="flex gap-3 overflow-x-auto pb-2">
        {HOMEWORK_TEMPLATES.map((tpl) => {
          const Icon = tpl.icon;
          const isSelected = selected === tpl.id;
          return (
            <Card
              key={tpl.id}
              onClick={() => onSelect(tpl)}
              className={`flex-shrink-0 w-40 p-3 cursor-pointer transition-all hover:border-primary/50 ${
                isSelected ? 'border-primary bg-primary/5 ring-1 ring-primary' : ''
              }`}
            >
              <Icon className={`h-5 w-5 mb-2 ${isSelected ? 'text-primary' : 'text-muted-foreground'}`} />
              <div className="font-medium text-sm">{t(tpl.labelKey)}</div>
              <div className="text-xs text-muted-foreground mt-1 line-clamp-2">{t(tpl.descriptionKey)}</div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
