'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { cn } from '@/lib/utils';
import { SelfAssessmentRating } from '@/lib/api/textbooks';
import { ThumbsUp, HelpCircle, AlertTriangle, CheckCircle2 } from 'lucide-react';

interface SelfAssessmentProps {
  onSubmit: (rating: SelfAssessmentRating) => Promise<void>;
  currentRating?: SelfAssessmentRating | null;
  className?: string;
}

interface RatingOption {
  value: SelfAssessmentRating;
  icon: React.ElementType;
  color: string;
  bgColor: string;
  borderColor: string;
  hoverColor: string;
}

const RATING_OPTIONS: RatingOption[] = [
  {
    value: 'understood',
    icon: ThumbsUp,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-300',
    hoverColor: 'hover:bg-green-100 hover:border-green-400',
  },
  {
    value: 'questions',
    icon: HelpCircle,
    color: 'text-amber-600',
    bgColor: 'bg-amber-50',
    borderColor: 'border-amber-300',
    hoverColor: 'hover:bg-amber-100 hover:border-amber-400',
  },
  {
    value: 'difficult',
    icon: AlertTriangle,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-300',
    hoverColor: 'hover:bg-red-100 hover:border-red-400',
  },
];

export function SelfAssessment({
  onSubmit,
  currentRating,
  className,
}: SelfAssessmentProps) {
  const t = useTranslations('paragraph');
  const [selectedRating, setSelectedRating] = useState<SelfAssessmentRating | null>(currentRating || null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(!!currentRating);

  const handleSelect = (rating: SelfAssessmentRating) => {
    if (isSubmitted) return;
    setSelectedRating(rating);
  };

  const handleSubmit = async () => {
    if (!selectedRating || isSubmitting || isSubmitted) return;

    setIsSubmitting(true);
    try {
      await onSubmit(selectedRating);
      setIsSubmitted(true);
    } catch (error) {
      console.error('Failed to submit self-assessment:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getRatingLabel = (rating: SelfAssessmentRating): string => {
    const labels: Record<SelfAssessmentRating, string> = {
      understood: t('selfAssessment.understood'),
      questions: t('selfAssessment.questions'),
      difficult: t('selfAssessment.difficult'),
    };
    return labels[rating];
  };

  const getRatingDescription = (rating: SelfAssessmentRating): string => {
    const descriptions: Record<SelfAssessmentRating, string> = {
      understood: t('selfAssessment.understoodDesc'),
      questions: t('selfAssessment.questionsDesc'),
      difficult: t('selfAssessment.difficultDesc'),
    };
    return descriptions[rating];
  };

  return (
    <div data-testid="self-assessment" className={cn('bg-white rounded-2xl shadow-md p-6', className)}>
      {/* Header */}
      <div className="text-center mb-6">
        <h3 data-testid="self-assessment-title" className="text-xl font-bold text-gray-900 mb-2">
          {t('selfAssessment.title')}
        </h3>
        <p className="text-gray-600">
          {t('selfAssessment.subtitle')}
        </p>
      </div>

      {/* Rating options */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {RATING_OPTIONS.map((option) => {
          const Icon = option.icon;
          const isSelected = selectedRating === option.value;
          const isCurrentlySubmitted = isSubmitted && currentRating === option.value;

          return (
            <button
              key={option.value}
              data-testid={`rating-${option.value}`}
              onClick={() => handleSelect(option.value)}
              disabled={isSubmitted}
              className={cn(
                'p-6 rounded-xl border-2 transition-all duration-200 text-center',
                isSelected && !isSubmitted && `${option.bgColor} ${option.borderColor}`,
                isCurrentlySubmitted && `${option.bgColor} ${option.borderColor} ring-2 ring-offset-2`,
                !isSelected && !isSubmitted && `border-gray-200 ${option.hoverColor}`,
                !isSelected && isSubmitted && 'border-gray-200 opacity-50',
                !isSubmitted && 'cursor-pointer active:scale-95',
                isSubmitted && 'cursor-default'
              )}
            >
              <div className={cn(
                'w-14 h-14 mx-auto rounded-full flex items-center justify-center mb-3',
                isSelected || isCurrentlySubmitted ? option.bgColor : 'bg-gray-100'
              )}>
                <Icon className={cn(
                  'w-7 h-7',
                  isSelected || isCurrentlySubmitted ? option.color : 'text-gray-400'
                )} />
              </div>

              <h4 className={cn(
                'font-semibold mb-1',
                isSelected || isCurrentlySubmitted ? option.color : 'text-gray-700'
              )}>
                {getRatingLabel(option.value)}
              </h4>

              <p className="text-sm text-gray-500">
                {getRatingDescription(option.value)}
              </p>
            </button>
          );
        })}
      </div>

      {/* Submit button or confirmation */}
      {!isSubmitted ? (
        <div className="text-center">
          <button
            data-testid="submit-assessment"
            onClick={handleSubmit}
            disabled={!selectedRating || isSubmitting}
            className={cn(
              'px-8 py-3 rounded-xl font-medium transition-all duration-200',
              selectedRating
                ? 'bg-amber-500 text-white hover:bg-amber-600 active:scale-95'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            )}
          >
            {isSubmitting ? t('selfAssessment.submitting') : t('selfAssessment.submit')}
          </button>
        </div>
      ) : (
        <div className="text-center">
          <div data-testid="assessment-submitted" className="inline-flex items-center gap-2 text-green-600 bg-green-50 px-4 py-2 rounded-full">
            <CheckCircle2 className="w-5 h-5" />
            <span className="font-medium">{t('selfAssessment.submitted')}</span>
          </div>
        </div>
      )}
    </div>
  );
}
