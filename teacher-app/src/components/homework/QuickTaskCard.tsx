'use client';

import { useTranslations } from 'next-intl';
import { Trash2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { TaskType } from '@/types/homework';
import type { ParagraphSearchResult } from '@/types/content';
import { ParagraphSearchCombobox } from './ParagraphSearchCombobox';

export interface QuickTaskDraft {
  id: string;
  taskType: TaskType;
  paragraph: ParagraphSearchResult | null;
  points: number;
  maxAttempts: number;
}

interface QuickTaskCardProps {
  task: QuickTaskDraft;
  index: number;
  onChange: (id: string, updates: Partial<QuickTaskDraft>) => void;
  onDelete: (id: string) => void;
  disabled?: boolean;
}

const TASK_TYPES = [
  TaskType.READ,
  TaskType.QUIZ,
  TaskType.OPEN_QUESTION,
  TaskType.ESSAY,
  TaskType.PRACTICE,
  TaskType.CODE,
];

export function QuickTaskCard({ task, index, onChange, onDelete, disabled }: QuickTaskCardProps) {
  const t = useTranslations('homework.task');

  return (
    <div className="rounded-lg border bg-card p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-muted-foreground">
          {t('title')} {index + 1}
        </span>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => onDelete(task.id)}
          disabled={disabled}
          className="h-7 w-7 p-0 text-muted-foreground hover:text-destructive"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-[180px_1fr] gap-3">
        <div className="space-y-1.5">
          <Label className="text-xs">{t('type')}</Label>
          <Select
            value={task.taskType}
            onValueChange={(v) => onChange(task.id, { taskType: v as TaskType })}
            disabled={disabled}
          >
            <SelectTrigger className="h-9">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {TASK_TYPES.map((type) => (
                <SelectItem key={type} value={type}>
                  {t(`types.${type}`)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label className="text-xs">{t('paragraph')}</Label>
          <ParagraphSearchCombobox
            value={task.paragraph}
            onSelect={(p) => onChange(task.id, { paragraph: p })}
            disabled={disabled}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 max-w-xs">
        <div className="space-y-1.5">
          <Label className="text-xs">{t('points')}</Label>
          <Input
            type="number"
            min={1}
            max={100}
            value={task.points}
            onChange={(e) => onChange(task.id, { points: Math.max(1, Math.min(100, Number(e.target.value) || 1)) })}
            disabled={disabled}
            className="h-9"
          />
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs">{t('maxAttempts')}</Label>
          <Input
            type="number"
            min={1}
            max={10}
            value={task.maxAttempts}
            onChange={(e) => onChange(task.id, { maxAttempts: Math.max(1, Math.min(10, Number(e.target.value) || 1)) })}
            disabled={disabled}
            className="h-9"
          />
        </div>
      </div>
    </div>
  );
}
