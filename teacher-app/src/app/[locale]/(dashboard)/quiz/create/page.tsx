'use client';

import { useTranslations } from 'next-intl';
import QuizCreateForm from '@/components/quiz/QuizCreateForm';

export default function QuizCreatePage() {
  const t = useTranslations('quiz');

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t('createQuiz')}</h1>
      <QuizCreateForm />
    </div>
  );
}
