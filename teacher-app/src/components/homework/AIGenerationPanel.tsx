'use client';

import { useState, useMemo } from 'react';
import { useTranslations } from 'next-intl';
import { Sparkles, Loader2, BookOpen, FileText, Edit3, Code, Briefcase } from 'lucide-react';
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
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { TaskType, QuestionType, BloomLevel, type GenerationParams } from '@/types/homework';

interface AIGenerationPanelProps {
  onGenerate: (params: GenerationParams) => void;
  isGenerating?: boolean;
  hasQuestions?: boolean;
  taskType?: TaskType;
}

/**
 * Configuration for each task type's generation UI
 */
const TASK_TYPE_CONFIG = {
  [TaskType.READ]: {
    icon: BookOpen,
    showQuestionTypes: false,
    showBloomLevels: false,
    showCount: false,
    showDifficulty: false,
    defaultCount: 3,
    defaultTypes: [QuestionType.SINGLE_CHOICE, QuestionType.TRUE_FALSE],
    defaultBloomLevels: [BloomLevel.REMEMBER, BloomLevel.UNDERSTAND],
    buttonTextKey: 'generateReadingCheck',
    descriptionKey: 'readingCheckDescription',
  },
  [TaskType.QUIZ]: {
    icon: Sparkles,
    showQuestionTypes: true,
    showBloomLevels: true,
    showCount: true,
    showDifficulty: true,
    defaultCount: 5,
    defaultTypes: [QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE],
    defaultBloomLevels: [BloomLevel.UNDERSTAND, BloomLevel.APPLY],
    buttonTextKey: 'generate',
    descriptionKey: 'quizDescription',
  },
  [TaskType.OPEN_QUESTION]: {
    icon: FileText,
    showQuestionTypes: false,
    showBloomLevels: true,
    showCount: true,
    showDifficulty: true,
    defaultCount: 3,
    defaultTypes: [QuestionType.OPEN_ENDED],
    defaultBloomLevels: [BloomLevel.UNDERSTAND, BloomLevel.APPLY, BloomLevel.ANALYZE],
    buttonTextKey: 'generateOpenQuestions',
    descriptionKey: 'openQuestionDescription',
  },
  [TaskType.ESSAY]: {
    icon: Edit3,
    showQuestionTypes: false,
    showBloomLevels: false,
    showCount: false,
    showDifficulty: true,
    defaultCount: 1,
    defaultTypes: [QuestionType.OPEN_ENDED],
    defaultBloomLevels: [BloomLevel.ANALYZE, BloomLevel.EVALUATE, BloomLevel.CREATE],
    buttonTextKey: 'generateEssayTopic',
    descriptionKey: 'essayDescription',
  },
  [TaskType.PRACTICE]: {
    icon: Briefcase,
    showQuestionTypes: false,
    showBloomLevels: true,
    showCount: true,
    showDifficulty: true,
    defaultCount: 2,
    defaultTypes: [QuestionType.OPEN_ENDED],
    defaultBloomLevels: [BloomLevel.APPLY, BloomLevel.ANALYZE],
    buttonTextKey: 'generatePractice',
    descriptionKey: 'practiceDescription',
  },
  [TaskType.CODE]: {
    icon: Code,
    showQuestionTypes: false,
    showBloomLevels: false,
    showCount: false,
    showDifficulty: true,
    defaultCount: 1,
    defaultTypes: [QuestionType.CODE],
    defaultBloomLevels: [BloomLevel.APPLY, BloomLevel.CREATE],
    buttonTextKey: 'generateCodeTask',
    descriptionKey: 'codeDescription',
  },
};

export function AIGenerationPanel({
  onGenerate,
  isGenerating,
  hasQuestions,
  taskType = TaskType.QUIZ,
}: AIGenerationPanelProps) {
  const t = useTranslations('homework.question');
  const tBloom = useTranslations('homework.question.bloomLevels');
  const tForm = useTranslations('homework.form');
  const tAI = useTranslations('homework.ai');

  const config = TASK_TYPE_CONFIG[taskType] || TASK_TYPE_CONFIG[TaskType.QUIZ];
  const Icon = config.icon;

  const [questionsCount, setQuestionsCount] = useState(config.defaultCount);
  const [language, setLanguage] = useState<'ru' | 'kz'>('ru');
  const [difficulty, setDifficulty] = useState<'easy' | 'medium' | 'hard'>('medium');
  const [selectedTypes, setSelectedTypes] = useState<QuestionType[]>(config.defaultTypes);
  const [selectedBloomLevels, setSelectedBloomLevels] = useState<BloomLevel[]>(
    config.defaultBloomLevels
  );

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
    // Use config defaults for hidden options
    const finalTypes = config.showQuestionTypes ? selectedTypes : config.defaultTypes;
    const finalBloomLevels = config.showBloomLevels ? selectedBloomLevels : config.defaultBloomLevels;
    const finalCount = config.showCount ? questionsCount : config.defaultCount;

    onGenerate({
      questions_count: finalCount,
      question_types: finalTypes,
      bloom_levels: finalBloomLevels,
      language,
      difficulty: config.showDifficulty ? difficulty : undefined,
      include_explanation: true,
    });
  };

  // Get button text based on task type
  const getButtonText = () => {
    if (isGenerating) {
      return t('generating');
    }
    if (hasQuestions) {
      return t('regenerate');
    }
    // Try task-type-specific key, fallback to 'generate'
    try {
      return tAI(config.buttonTextKey);
    } catch {
      return t('generate');
    }
  };

  // Get description based on task type
  const getDescription = () => {
    try {
      return tAI(config.descriptionKey);
    } catch {
      return null;
    }
  };

  const description = getDescription();

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <Icon className="h-4 w-4 text-primary" />
          AI {t('title')}
        </CardTitle>
        {description && (
          <CardDescription className="text-xs">
            {description}
          </CardDescription>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Count and Language - show count only if config allows */}
        <div className={`grid gap-4 ${config.showCount ? 'grid-cols-2' : 'grid-cols-1'}`}>
          {config.showCount && (
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
                  {[2, 3, 5, 7, 10, 15, 20].map((n) => (
                    <SelectItem key={n} value={n.toString()}>
                      {n}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

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

        {/* Difficulty - show only if config allows */}
        {config.showDifficulty && (
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
        )}

        {/* Question Types - show only for QUIZ */}
        {config.showQuestionTypes && (
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
        )}

        {/* Bloom Levels - show for QUIZ, OPEN_QUESTION, PRACTICE */}
        {config.showBloomLevels && (
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
        )}

        {/* Generate Button */}
        <Button
          onClick={handleGenerate}
          disabled={isGenerating || (config.showQuestionTypes && selectedTypes.length === 0)}
          className="w-full"
        >
          {isGenerating ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
              {getButtonText()}
            </>
          ) : (
            <>
              <Icon className="h-4 w-4 mr-2" />
              {getButtonText()}
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
