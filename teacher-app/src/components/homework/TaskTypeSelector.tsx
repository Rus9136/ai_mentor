'use client';

import { useTranslations } from 'next-intl';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { TaskType } from '@/types/homework';

interface TaskTypeSelectorProps {
  value: TaskType;
  onChange: (value: TaskType) => void;
  disabled?: boolean;
}

export function TaskTypeSelector({ value, onChange, disabled }: TaskTypeSelectorProps) {
  const t = useTranslations('homework.task.types');

  const taskTypes: TaskType[] = [
    TaskType.READ,
    TaskType.QUIZ,
    TaskType.OPEN_QUESTION,
    TaskType.ESSAY,
    TaskType.PRACTICE,
    TaskType.CODE,
  ];

  return (
    <Select value={value} onValueChange={onChange as (value: string) => void} disabled={disabled}>
      <SelectTrigger>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {taskTypes.map((type) => (
          <SelectItem key={type} value={type}>
            {t(type)}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
