'use client';

import { useState, useEffect } from 'react';
import {
  Layers,
  Plus,
  Save,
  Trash2,
  GripVertical,
  Loader2,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { StatusBadge } from './status-badge';
import type { ParagraphContent, CardItem, CardType } from '@/types';

interface CardsSectionProps {
  content: ParagraphContent | null | undefined;
  paragraphId: number;
  language: string;
  onSave: (cards: CardItem[]) => void;
  isLoading?: boolean;
}

const CARD_TYPES: { value: CardType; label: string }[] = [
  { value: 'term', label: 'Термин' },
  { value: 'fact', label: 'Факт' },
  { value: 'check', label: 'Проверочный' },
];

function generateId(): string {
  return `card-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

export function CardsSection({
  content,
  paragraphId,
  language,
  onSave,
  isLoading = false,
}: CardsSectionProps) {
  const [cards, setCards] = useState<CardItem[]>([]);
  const [isDirty, setIsDirty] = useState(false);

  // Sync local state with content
  useEffect(() => {
    setCards(content?.cards || []);
    setIsDirty(false);
  }, [content?.cards, paragraphId, language]);

  const handleAddCard = () => {
    const newCard: CardItem = {
      id: generateId(),
      type: 'term',
      front: '',
      back: '',
      order: cards.length + 1,
    };
    setCards([...cards, newCard]);
    setIsDirty(true);
  };

  const handleUpdateCard = (id: string, field: keyof CardItem, value: string | number) => {
    setCards(
      cards.map((card) =>
        card.id === id ? { ...card, [field]: value } : card
      )
    );
    setIsDirty(true);
  };

  const handleDeleteCard = (id: string) => {
    const newCards = cards
      .filter((card) => card.id !== id)
      .map((card, index) => ({ ...card, order: index + 1 }));
    setCards(newCards);
    setIsDirty(true);
  };

  const handleMoveCard = (id: string, direction: 'up' | 'down') => {
    const index = cards.findIndex((card) => card.id === id);
    if (
      (direction === 'up' && index === 0) ||
      (direction === 'down' && index === cards.length - 1)
    ) {
      return;
    }

    const newCards = [...cards];
    const newIndex = direction === 'up' ? index - 1 : index + 1;
    [newCards[index], newCards[newIndex]] = [newCards[newIndex], newCards[index]];

    // Update order
    newCards.forEach((card, i) => {
      card.order = i + 1;
    });

    setCards(newCards);
    setIsDirty(true);
  };

  const handleSave = () => {
    onSave(cards);
    setIsDirty(false);
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center gap-2">
          <Layers className="h-5 w-5 text-muted-foreground" />
          <CardTitle className="text-lg">Карточки</CardTitle>
          <span className="text-sm text-muted-foreground">
            ({cards.length})
          </span>
        </div>
        <StatusBadge status={content?.status_cards || 'empty'} />
      </CardHeader>
      <CardContent className="space-y-4">
        {cards.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Layers className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>Нет карточек</p>
            <p className="text-sm">Добавьте карточки для повторения материала</p>
          </div>
        ) : (
          <div className="space-y-4">
            {cards.map((card, index) => (
              <CardEditor
                key={card.id}
                card={card}
                index={index}
                total={cards.length}
                onUpdate={(field, value) => handleUpdateCard(card.id, field, value)}
                onDelete={() => handleDeleteCard(card.id)}
                onMove={(direction) => handleMoveCard(card.id, direction)}
              />
            ))}
          </div>
        )}

        <div className="flex justify-between pt-4 border-t">
          <Button variant="outline" onClick={handleAddCard}>
            <Plus className="h-4 w-4 mr-2" />
            Добавить карточку
          </Button>
          <Button onClick={handleSave} disabled={!isDirty || isLoading}>
            {isLoading ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Save className="h-4 w-4 mr-2" />
            )}
            Сохранить
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// Individual card editor component
interface CardEditorProps {
  card: CardItem;
  index: number;
  total: number;
  onUpdate: (field: keyof CardItem, value: string | number) => void;
  onDelete: () => void;
  onMove: (direction: 'up' | 'down') => void;
}

function CardEditor({
  card,
  index,
  total,
  onUpdate,
  onDelete,
  onMove,
}: CardEditorProps) {
  return (
    <div className="border rounded-lg p-4 space-y-4 bg-muted/30">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <GripVertical className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium text-sm">Карточка #{index + 1}</span>
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => onMove('up')}
            disabled={index === 0}
          >
            <span className="sr-only">Вверх</span>
            ↑
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => onMove('down')}
            disabled={index === total - 1}
          >
            <span className="sr-only">Вниз</span>
            ↓
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-destructive hover:text-destructive"
            onClick={onDelete}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label>Тип карточки</Label>
          <Select
            value={card.type}
            onValueChange={(value) => onUpdate('type', value as CardType)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {CARD_TYPES.map((type) => (
                <SelectItem key={type.value} value={type.value}>
                  {type.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label>Лицевая сторона (вопрос/термин)</Label>
          <Textarea
            value={card.front}
            onChange={(e) => onUpdate('front', e.target.value)}
            placeholder={
              card.type === 'term'
                ? 'Термин'
                : card.type === 'fact'
                ? 'Вопрос о факте'
                : 'Проверочный вопрос'
            }
            className="min-h-[80px]"
          />
        </div>
        <div className="space-y-2">
          <Label>Обратная сторона (ответ/определение)</Label>
          <Textarea
            value={card.back}
            onChange={(e) => onUpdate('back', e.target.value)}
            placeholder={
              card.type === 'term'
                ? 'Определение термина'
                : 'Ответ'
            }
            className="min-h-[80px]"
          />
        </div>
      </div>
    </div>
  );
}
