'use client';

import { useTranslations } from 'next-intl';
import FactileCreateForm from '@/components/quiz/FactileCreateForm';

export default function FactileCreatePage() {
  const t = useTranslations('quiz');

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t('factileTitle')}</h1>
        <p className="text-sm text-muted-foreground mt-1">{t('factileDescription')}</p>
      </div>
      <FactileCreateForm />
    </div>
  );
}
