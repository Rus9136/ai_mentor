'use client';

import { useState, useEffect } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { Question, QuestionType, QuestionCreate, QuestionOptionCreate } from '@/types/test';

interface QuestionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  question?: Question;
  nextOrder: number;
  onSubmit: (data: QuestionCreate) => void;
  isLoading?: boolean;
}

const QUESTION_TYPES: { value: QuestionType; label: string }[] = [
  { value: 'single_choice', label: 'Один правильный ответ' },
  { value: 'multiple_choice', label: 'Несколько правильных ответов' },
  { value: 'true_false', label: 'Верно / Неверно' },
  { value: 'short_answer', label: 'Краткий ответ' },
];

export function QuestionDialog({
  open,
  onOpenChange,
  question,
  nextOrder,
  onSubmit,
  isLoading,
}: QuestionDialogProps) {
  const isEdit = !!question;

  const [questionType, setQuestionType] = useState<QuestionType>('single_choice');
  const [questionText, setQuestionText] = useState('');
  const [explanation, setExplanation] = useState('');
  const [points, setPoints] = useState(1);
  const [sortOrder, setSortOrder] = useState(1);
  const [options, setOptions] = useState<QuestionOptionCreate[]>([
    { sort_order: 1, option_text: '', is_correct: true },
    { sort_order: 2, option_text: '', is_correct: false },
  ]);

  // Reset form when dialog opens
  useEffect(() => {
    if (open) {
      if (question) {
        setQuestionType(question.question_type);
        setQuestionText(question.question_text);
        setExplanation(question.explanation || '');
        setPoints(question.points);
        setSortOrder(question.sort_order);
        setOptions(
          question.options.map((o) => ({
            sort_order: o.sort_order,
            option_text: o.option_text,
            is_correct: o.is_correct,
          }))
        );
      } else {
        setQuestionType('single_choice');
        setQuestionText('');
        setExplanation('');
        setPoints(1);
        setSortOrder(nextOrder + 1);
        setOptions([
          { sort_order: 1, option_text: '', is_correct: true },
          { sort_order: 2, option_text: '', is_correct: false },
        ]);
      }
    }
  }, [open, question, nextOrder]);

  // Handle true/false type
  useEffect(() => {
    if (questionType === 'true_false' && !isEdit) {
      setOptions([
        { sort_order: 1, option_text: 'Верно', is_correct: true },
        { sort_order: 2, option_text: 'Неверно', is_correct: false },
      ]);
    }
  }, [questionType, isEdit]);

  const addOption = () => {
    setOptions((prev) => [
      ...prev,
      { sort_order: prev.length + 1, option_text: '', is_correct: false },
    ]);
  };

  const removeOption = (index: number) => {
    setOptions((prev) => prev.filter((_, i) => i !== index));
  };

  const updateOption = (index: number, field: keyof QuestionOptionCreate, value: string | boolean | number) => {
    setOptions((prev) =>
      prev.map((opt, i) => (i === index ? { ...opt, [field]: value } : opt))
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!questionText.trim()) return;

    onSubmit({
      sort_order: sortOrder,
      question_type: questionType,
      question_text: questionText.trim(),
      explanation: explanation.trim() || undefined,
      points,
      options: questionType !== 'short_answer' ? options : undefined,
    });
  };

  const showOptions = questionType !== 'short_answer';

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEdit ? 'Редактировать вопрос' : 'Добавить вопрос'}</DialogTitle>
          <DialogDescription>
            {isEdit ? 'Измените параметры вопроса' : 'Заполните информацию о новом вопросе'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label>Тип вопроса *</Label>
              <Select value={questionType} onValueChange={(v) => setQuestionType(v as QuestionType)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {QUESTION_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Баллы *</Label>
              <Input
                type="number"
                min={1}
                max={100}
                value={points}
                onChange={(e) => setPoints(parseInt(e.target.value) || 1)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Текст вопроса *</Label>
            <Textarea
              value={questionText}
              onChange={(e) => setQuestionText(e.target.value)}
              placeholder="Введите текст вопроса..."
              className="min-h-[100px]"
            />
          </div>

          {showOptions && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label>Варианты ответов</Label>
                {questionType !== 'true_false' && (
                  <Button type="button" variant="outline" size="sm" onClick={addOption}>
                    <Plus className="mr-2 h-4 w-4" />
                    Добавить вариант
                  </Button>
                )}
              </div>

              <div className="space-y-3">
                {options.map((opt, index) => (
                  <div key={index} className="flex items-start gap-3 rounded-lg border p-3">
                    <div className="flex items-center pt-2">
                      <Checkbox
                        checked={opt.is_correct}
                        onCheckedChange={(checked) =>
                          updateOption(index, 'is_correct', checked === true)
                        }
                      />
                    </div>
                    <div className="flex-1">
                      <Input
                        placeholder={`Вариант ${index + 1}`}
                        value={opt.option_text}
                        onChange={(e) => updateOption(index, 'option_text', e.target.value)}
                        disabled={questionType === 'true_false'}
                      />
                    </div>
                    {questionType !== 'true_false' && options.length > 2 && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={() => removeOption(index)}
                        className="text-destructive hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                ))}
              </div>
              <p className="text-sm text-muted-foreground">
                Отметьте галочкой правильные варианты ответа
              </p>
            </div>
          )}

          <div className="space-y-2">
            <Label>Пояснение (необязательно)</Label>
            <Textarea
              value={explanation}
              onChange={(e) => setExplanation(e.target.value)}
              placeholder="Пояснение к правильному ответу..."
              className="min-h-[80px]"
            />
            <p className="text-sm text-muted-foreground">
              Будет показано ученику после ответа на вопрос
            </p>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Отмена
            </Button>
            <Button type="submit" disabled={isLoading || !questionText.trim()}>
              {isLoading ? 'Сохранение...' : isEdit ? 'Сохранить' : 'Добавить'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
