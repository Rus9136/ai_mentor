'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Sparkles, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { QuestionType, BloomLevel, type GenerationParams } from '@/types/homework';

interface AIGenerationPanelProps {
  onGenerate: (params: GenerationParams) => void;
  isGenerating?: boolean;
  hasQuestions?: boolean;
}

export function AIGenerationPanel({
  onGenerate,
  isGenerating,
  hasQuestions,
}: AIGenerationPanelProps) {
  const t = useTranslations('homework.question');
  const tBloom = useTranslations('homework.question.bloomLevels');
  const tForm = useTranslations('homework.form');

  const [questionsCount, setQuestionsCount] = useState(5);
  const [language, setLanguage] = useState<'ru' | 'kz'>('ru');
  const [difficulty, setDifficulty] = useState<'easy' | 'medium' | 'hard'>('medium');
  const [selectedTypes, setSelectedTypes] = useState<QuestionType[]>([
    QuestionType.SINGLE_CHOICE,
    QuestionType.MULTIPLE_CHOICE,
  ]);
  const [selectedBloomLevels, setSelectedBloomLevels] = useState<BloomLevel[]>([
    BloomLevel.UNDERSTAND,
    BloomLevel.APPLY,
  ]);

  const questionTypes: QuestionType[] = [
    QuestionType.SINGLE_CHOICE,
    QuestionType.MULTIPLE_CHOICE,
    QuestionType.TRUE_FALSE,
    QuestionType.SHORT_ANSWER,
    QuestionType.OPEN_ENDED,
  ];

  const bloomLevels: BloomLevel[] = [
    BloomLevel.REMEMBER,
    BloomLevel.UNDERSTAND,
    BloomLevel.APPLY,
    BloomLevel.ANALYZE,
    BloomLevel.EVALUATE,
    BloomLevel.CREATE,
  ];

  const toggleType = (type: QuestionType) => {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  const toggleBloomLevel = (level: BloomLevel) => {
    setSelectedBloomLevels((prev) =>
      prev.includes(level) ? prev.filter((l) => l !== level) : [...prev, level]
    );
  };

  const handleGenerate = () => {
    onGenerate({
      questions_count: questionsCount,
      question_types: selectedTypes,
      bloom_levels: selectedBloomLevels,
      language,
      difficulty,
      include_explanation: true,
    });
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          AI {t('title')}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Count and Language */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>{t('count')}</Label>
            <Select
              value={questionsCount.toString()}
              onValueChange={(v) => setQuestionsCount(Number(v))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {[3, 5, 7, 10, 15, 20].map((n) => (
                  <SelectItem key={n} value={n.toString()}>
                    {n}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>{t('language')}</Label>
            <Select value={language} onValueChange={(v) => setLanguage(v as 'ru' | 'kz')}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ru">{t('russian')}</SelectItem>
                <SelectItem value="kz">{t('kazakh')}</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Difficulty */}
        <div className="space-y-2">
          <Label>{t('difficulty')}</Label>
          <Select
            value={difficulty}
            onValueChange={(v) => setDifficulty(v as 'easy' | 'medium' | 'hard')}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="easy">
                {tForm('difficultyEasy')}
              </SelectItem>
              <SelectItem value="medium">
                {tForm('difficultyMedium')}
              </SelectItem>
              <SelectItem value="hard">
                {tForm('difficultyHard')}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Question Types */}
        <div className="space-y-2">
          <Label>{t('title')}</Label>
          <div className="flex flex-wrap gap-3">
            {questionTypes.map((type) => (
              <label key={type} className="flex items-center gap-2 text-sm cursor-pointer">
                <Checkbox
                  checked={selectedTypes.includes(type)}
                  onCheckedChange={() => toggleType(type)}
                />
                {t(`types.${type}`)}
              </label>
            ))}
          </div>
        </div>

        {/* Bloom Levels */}
        <div className="space-y-2">
          <Label>{tBloom('title')}</Label>
          <div className="flex flex-wrap gap-3">
            {bloomLevels.map((level) => (
              <label key={level} className="flex items-center gap-2 text-sm cursor-pointer">
                <Checkbox
                  checked={selectedBloomLevels.includes(level)}
                  onCheckedChange={() => toggleBloomLevel(level)}
                />
                {tBloom(level)}
              </label>
            ))}
          </div>
        </div>

        {/* Generate Button */}
        <Button
          onClick={handleGenerate}
          disabled={isGenerating || selectedTypes.length === 0}
          className="w-full"
        >
          {isGenerating ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
              {t('generating')}
            </>
          ) : hasQuestions ? (
            <>
              <Sparkles className="h-4 w-4 mr-2" />
              {t('regenerate')}
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4 mr-2" />
              {t('generate')}
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
