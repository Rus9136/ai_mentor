'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
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
import { Checkbox } from '@/components/ui/checkbox';
import { useTextbooks, useChapters, useParagraphs } from '@/lib/hooks/use-content';
import type { Test, TestCreate, DifficultyLevel, TestPurpose } from '@/types/test';

interface TestFormProps {
  test?: Test;
  onSubmit: (data: TestCreate) => void;
  isLoading?: boolean;
}

const TEST_PURPOSES: { value: TestPurpose; label: string }[] = [
  { value: 'diagnostic', label: 'Диагностический' },
  { value: 'formative', label: 'Формативный' },
  { value: 'summative', label: 'Суммативный' },
  { value: 'practice', label: 'Практический' },
];

const DIFFICULTIES: { value: DifficultyLevel; label: string }[] = [
  { value: 'easy', label: 'Легкий' },
  { value: 'medium', label: 'Средний' },
  { value: 'hard', label: 'Сложный' },
];

export function TestForm({ test, onSubmit, isLoading }: TestFormProps) {
  const [title, setTitle] = useState(test?.title ?? '');
  const [description, setDescription] = useState(test?.description ?? '');
  const [textbookId, setTextbookId] = useState<number>(test?.textbook_id ?? 0);
  const [chapterId, setChapterId] = useState<number | undefined>(test?.chapter_id ?? undefined);
  const [paragraphId, setParagraphId] = useState<number | undefined>(test?.paragraph_id ?? undefined);
  const [testPurpose, setTestPurpose] = useState<TestPurpose>(test?.test_purpose ?? 'formative');
  const [difficulty, setDifficulty] = useState<DifficultyLevel>(test?.difficulty ?? 'medium');
  const [timeLimit, setTimeLimit] = useState<number | undefined>(test?.time_limit ?? undefined);
  const [passingScore, setPassingScore] = useState<number>(test?.passing_score ?? 70);
  const [isActive, setIsActive] = useState<boolean>(test?.is_active ?? true);

  const { data: textbooks = [], isLoading: textbooksLoading } = useTextbooks();
  const { data: chapters = [], isLoading: chaptersLoading } = useChapters(textbookId);
  const { data: paragraphs = [], isLoading: paragraphsLoading } = useParagraphs(chapterId ?? 0);

  // Reset chapter/paragraph when textbook changes
  useEffect(() => {
    if (!test) {
      setChapterId(undefined);
      setParagraphId(undefined);
    }
  }, [textbookId, test]);

  useEffect(() => {
    if (!test) {
      setParagraphId(undefined);
    }
  }, [chapterId, test]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !textbookId) return;

    onSubmit({
      title: title.trim(),
      description: description.trim() || undefined,
      textbook_id: textbookId,
      chapter_id: chapterId ?? null,
      paragraph_id: paragraphId ?? null,
      test_purpose: testPurpose,
      difficulty,
      time_limit: timeLimit,
      passing_score: passingScore,
      is_active: isActive,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="title">Название теста *</Label>
        <Input
          id="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Тест по главе 1: Числа и выражения"
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Описание</Label>
        <Textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Описание теста..."
          className="min-h-[80px]"
        />
      </div>

      {/* Cascading content selects */}
      <div className="space-y-4 rounded-lg border p-4">
        <h3 className="font-medium">Привязка к контенту</h3>
        <div className="grid gap-4 md:grid-cols-3">
          <div className="space-y-2">
            <Label>Учебник *</Label>
            <Select
              value={textbookId ? String(textbookId) : undefined}
              onValueChange={(v) => setTextbookId(parseInt(v))}
              disabled={textbooksLoading}
            >
              <SelectTrigger className="w-full h-auto min-h-9 whitespace-normal text-left [&>span]:line-clamp-2">
                <SelectValue placeholder={textbooksLoading ? 'Загрузка...' : 'Выберите учебник'} />
              </SelectTrigger>
              <SelectContent>
                {textbooks.map((tb) => (
                  <SelectItem key={tb.id} value={String(tb.id)}>
                    {tb.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Глава</Label>
            <Select
              value={chapterId ? String(chapterId) : 'none'}
              onValueChange={(v) => setChapterId(v === 'none' ? undefined : parseInt(v))}
              disabled={!textbookId || chaptersLoading}
            >
              <SelectTrigger className="w-full h-auto min-h-9 whitespace-normal text-left [&>span]:line-clamp-2">
                <SelectValue
                  placeholder={
                    !textbookId
                      ? 'Сначала выберите учебник'
                      : chaptersLoading
                        ? 'Загрузка...'
                        : 'Выберите главу'
                  }
                />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">Без привязки к главе</SelectItem>
                {chapters.map((ch) => (
                  <SelectItem key={ch.id} value={String(ch.id)}>
                    {ch.number}. {ch.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Параграф</Label>
            <Select
              value={paragraphId ? String(paragraphId) : 'none'}
              onValueChange={(v) => setParagraphId(v === 'none' ? undefined : parseInt(v))}
              disabled={!chapterId || paragraphsLoading}
            >
              <SelectTrigger className="w-full h-auto min-h-9 whitespace-normal text-left [&>span]:line-clamp-2">
                <SelectValue
                  placeholder={
                    !chapterId
                      ? 'Сначала выберите главу'
                      : paragraphsLoading
                        ? 'Загрузка...'
                        : 'Выберите параграф'
                  }
                />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">Без привязки к параграфу</SelectItem>
                {paragraphs.map((p) => (
                  <SelectItem key={p.id} value={String(p.id)}>
                    {p.number}. {p.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="space-y-2">
          <Label>Назначение *</Label>
          <Select value={testPurpose} onValueChange={(v) => setTestPurpose(v as TestPurpose)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {TEST_PURPOSES.map((p) => (
                <SelectItem key={p.value} value={p.value}>
                  {p.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Сложность *</Label>
          <Select value={difficulty} onValueChange={(v) => setDifficulty(v as DifficultyLevel)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {DIFFICULTIES.map((d) => (
                <SelectItem key={d.value} value={d.value}>
                  {d.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="timeLimit">Ограничение по времени (мин)</Label>
          <Input
            id="timeLimit"
            type="number"
            min={1}
            max={180}
            placeholder="30"
            value={timeLimit ?? ''}
            onChange={(e) => setTimeLimit(e.target.value ? parseInt(e.target.value) : undefined)}
          />
          <p className="text-sm text-muted-foreground">1-180 минут (необязательно)</p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="passingScore">Проходной балл (%) *</Label>
          <Input
            id="passingScore"
            type="number"
            min={0}
            max={100}
            value={passingScore}
            onChange={(e) => setPassingScore(parseInt(e.target.value) || 0)}
          />
          <p className="text-sm text-muted-foreground">Минимум % для прохождения</p>
        </div>
      </div>

      <div className="flex items-center gap-3 rounded-lg border p-4">
        <Checkbox
          id="isActive"
          checked={isActive}
          onCheckedChange={(checked) => setIsActive(checked === true)}
        />
        <div>
          <Label htmlFor="isActive" className="text-base cursor-pointer">
            Активен
          </Label>
          <p className="text-sm text-muted-foreground">
            Неактивные тесты не отображаются для учеников
          </p>
        </div>
      </div>

      <div className="flex justify-end gap-4">
        <Button type="submit" disabled={isLoading || !title.trim() || !textbookId}>
          {isLoading ? 'Сохранение...' : 'Сохранить'}
        </Button>
      </div>
    </form>
  );
}
