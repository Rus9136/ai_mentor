'use client';

import { useTranslations } from 'next-intl';
import { cn } from '@/lib/utils';
import { ParagraphStep } from '@/lib/api/textbooks';
import { BookOpen, FileText, Brain, CheckCircle2, Play } from 'lucide-react';

interface StepIndicatorProps {
  currentStep: ParagraphStep;
  availableSteps: ParagraphStep[];
  onStepChange: (step: ParagraphStep) => void;
  isCompleted?: boolean;
  className?: string;
}

const STEP_CONFIG: Record<ParagraphStep, { icon: React.ElementType; order: number }> = {
  intro: { icon: Play, order: 0 },
  content: { icon: BookOpen, order: 1 },
  practice: { icon: Brain, order: 2 },
  summary: { icon: FileText, order: 3 },
  completed: { icon: CheckCircle2, order: 4 },
};

export function StepIndicator({
  currentStep,
  availableSteps,
  onStepChange,
  isCompleted = false,
  className,
}: StepIndicatorProps) {
  const t = useTranslations('paragraph');

  // Filter and sort steps by order
  const sortedSteps = availableSteps
    .filter(step => step !== 'completed')
    .sort((a, b) => STEP_CONFIG[a].order - STEP_CONFIG[b].order);

  // Handle 'completed' step - show last step as current
  const effectiveCurrentStep = currentStep === 'completed'
    ? sortedSteps[sortedSteps.length - 1]
    : currentStep;
  const currentStepIndex = sortedSteps.indexOf(effectiveCurrentStep);

  const getStepStatus = (step: ParagraphStep, index: number): 'completed' | 'current' | 'upcoming' => {
    if (isCompleted || index < currentStepIndex) return 'completed';
    if (step === effectiveCurrentStep) return 'current';
    return 'upcoming';
  };

  const canNavigateToStep = (index: number): boolean => {
    // Can navigate to completed steps or one step ahead
    return index <= currentStepIndex + 1;
  };

  const getStepLabel = (step: ParagraphStep): string => {
    const labels: Record<ParagraphStep, string> = {
      intro: t('steps.intro'),
      content: t('steps.content'),
      practice: t('steps.practice'),
      summary: t('steps.summary'),
      completed: t('steps.completed'),
    };
    return labels[step];
  };

  return (
    <div className={cn('w-full', className)}>
      {/* Mobile: Compact horizontal */}
      <div className="flex items-center justify-between md:hidden">
        {sortedSteps.map((step, index) => {
          const status = getStepStatus(step, index);
          const Icon = STEP_CONFIG[step].icon;
          const canNavigate = canNavigateToStep(index);

          return (
            <div key={step} className="flex flex-col items-center flex-1">
              {/* Step circle */}
              <button
                onClick={() => canNavigate && onStepChange(step)}
                disabled={!canNavigate}
                className={cn(
                  'w-10 h-10 rounded-full flex items-center justify-center transition-all duration-200',
                  status === 'completed' && 'bg-green-500 text-white',
                  status === 'current' && 'bg-amber-500 text-white ring-4 ring-amber-200',
                  status === 'upcoming' && 'bg-gray-200 text-gray-400',
                  canNavigate && status !== 'current' && 'cursor-pointer hover:scale-110',
                  !canNavigate && 'cursor-not-allowed'
                )}
              >
                <Icon className="w-5 h-5" />
              </button>

              {/* Step label */}
              <span className={cn(
                'text-xs mt-1 text-center',
                status === 'current' ? 'font-semibold text-amber-600' : 'text-gray-500'
              )}>
                {getStepLabel(step)}
              </span>

              {/* Connector line (except last) */}
              {index < sortedSteps.length - 1 && (
                <div className="absolute hidden" /> // Mobile doesn't show connectors
              )}
            </div>
          );
        })}
      </div>

      {/* Desktop: Full horizontal with connectors */}
      <div className="hidden md:flex items-center">
        {sortedSteps.map((step, index) => {
          const status = getStepStatus(step, index);
          const Icon = STEP_CONFIG[step].icon;
          const canNavigate = canNavigateToStep(index);

          return (
            <div key={step} className="flex items-center flex-1">
              {/* Step */}
              <div className="flex flex-col items-center">
                <button
                  onClick={() => canNavigate && onStepChange(step)}
                  disabled={!canNavigate}
                  className={cn(
                    'w-12 h-12 rounded-full flex items-center justify-center transition-all duration-200',
                    status === 'completed' && 'bg-green-500 text-white',
                    status === 'current' && 'bg-amber-500 text-white ring-4 ring-amber-200 scale-110',
                    status === 'upcoming' && 'bg-gray-200 text-gray-400',
                    canNavigate && status !== 'current' && 'cursor-pointer hover:scale-105 hover:bg-amber-100',
                    !canNavigate && 'cursor-not-allowed'
                  )}
                  title={getStepLabel(step)}
                >
                  <Icon className="w-6 h-6" />
                </button>

                <span className={cn(
                  'text-sm mt-2',
                  status === 'completed' && 'text-green-600 font-medium',
                  status === 'current' && 'text-amber-600 font-semibold',
                  status === 'upcoming' && 'text-gray-400'
                )}>
                  {getStepLabel(step)}
                </span>
              </div>

              {/* Connector line */}
              {index < sortedSteps.length - 1 && (
                <div className="flex-1 mx-2">
                  <div className={cn(
                    'h-1 rounded-full transition-colors duration-300',
                    index < currentStepIndex ? 'bg-green-500' : 'bg-gray-200'
                  )} />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Progress text */}
      <div className="mt-4 text-center">
        <p className="text-sm text-gray-500">
          {t('stepProgress', {
            current: currentStepIndex + 1,
            total: sortedSteps.length,
          })}
        </p>
      </div>
    </div>
  );
}
