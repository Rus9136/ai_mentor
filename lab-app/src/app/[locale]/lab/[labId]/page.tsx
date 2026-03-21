'use client';

import { use } from 'react';
import { useTranslations } from 'next-intl';
import { useAuth } from '@/providers/auth-provider';
import { ArrowLeft } from 'lucide-react';
import { Link } from '@/i18n/routing';
import dynamic from 'next/dynamic';

const HistoryLab = dynamic(() => import('@/components/history/HistoryLab'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-screen">
      <div className="text-muted-foreground">Loading map...</div>
    </div>
  ),
});

const ChemistryLab = dynamic(() => import('@/components/chemistry/ChemistryLab'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-screen">
      <div className="text-muted-foreground">Loading 3D...</div>
    </div>
  ),
});

// Lab ID → component mapping
const LAB_COMPONENTS: Record<number, React.ComponentType> = {
  1: HistoryLab,
  2: ChemistryLab,
};

interface LabPageProps {
  params: Promise<{ labId: string }>;
}

export default function LabPage({ params }: LabPageProps) {
  const { labId } = use(params);
  const t = useTranslations();
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-muted-foreground">{t('common.loading')}</div>
      </div>
    );
  }

  if (!user) return null;

  const labIdNum = parseInt(labId);
  const LabComponent = LAB_COMPONENTS[labIdNum];

  if (!LabComponent) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <p className="text-muted-foreground">{t('lab.empty')}</p>
        <Link href="/" className="btn-pill btn-primary text-sm py-2 px-4 inline-flex items-center gap-2">
          <ArrowLeft className="w-4 h-4" />
          {t('common.back')}
        </Link>
      </div>
    );
  }

  return <LabComponent />;
}
