'use client';

import { useTranslations } from 'next-intl';
import { useAuth } from '@/providers/auth-provider';
import { FlaskConical, Map, Atom, Zap, Leaf } from 'lucide-react';
import { Link } from '@/i18n/routing';

const DEMO_LABS = [
  {
    id: 1,
    title: { ru: 'История Казахстана', kz: 'Қазақстан тарихы' },
    description: {
      ru: 'Интерактивная карта с таймлайном эпох — от саков до независимости',
      kz: 'Дәуірлер уақыт сызығы бар интерактивті карта — сақтардан тәуелсіздікке дейін',
    },
    icon: Map,
    color: 'bg-amber-500',
    lab_type: 'map' as const,
    available: true,
  },
  {
    id: 2,
    title: { ru: 'Химия — Молекулы', kz: 'Химия — Молекулалар' },
    description: {
      ru: '3D модели молекул — вращай, изучай связи, смотри реакции',
      kz: 'Молекулалардың 3D модельдері — айналдыр, байланыстарды зертте',
    },
    icon: Atom,
    color: 'bg-blue-500',
    lab_type: 'molecule_3d' as const,
    available: false,
  },
  {
    id: 3,
    title: { ru: 'Физика — Симуляции', kz: 'Физика — Симуляциялар' },
    description: {
      ru: 'Маятник, электрические цепи, оптика — меняй параметры и наблюдай',
      kz: 'Маятник, электр тізбектері, оптика — параметрлерді өзгерт және бақыла',
    },
    icon: Zap,
    color: 'bg-purple-500',
    lab_type: 'simulation' as const,
    available: false,
  },
  {
    id: 4,
    title: { ru: 'Биология — Анатомия', kz: 'Биология — Анатомия' },
    description: {
      ru: 'Интерактивная анатомия — слои тканей, клетки, системы органов',
      kz: 'Интерактивті анатомия — тін қабаттары, жасушалар, ағза жүйелері',
    },
    icon: Leaf,
    color: 'bg-green-500',
    lab_type: 'anatomy' as const,
    available: false,
  },
];

export default function CatalogPage() {
  const t = useTranslations();
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-muted-foreground">{t('common.loading')}</div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-muted-foreground">{t('common.loading')}</div>
      </div>
    );
  }

  // Detect locale from URL
  const locale = (typeof window !== 'undefined' && window.location.pathname.startsWith('/kz')) ? 'kz' : 'ru';
  const langKey = locale === 'kz' ? 'kz' : 'ru';

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-border bg-card/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center">
              <FlaskConical className="w-5 h-5 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-lg font-bold">{t('lab.title')}</h1>
              <p className="text-xs text-muted-foreground">{t('lab.subtitle')}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              {user.first_name}
            </span>
          </div>
        </div>
      </header>

      {/* Catalog */}
      <main className="max-w-5xl mx-auto px-4 py-8">
        <h2 className="text-xl font-bold mb-6">{t('lab.catalog')}</h2>

        <div className="grid gap-4 sm:grid-cols-2">
          {DEMO_LABS.map((lab) => {
            const Icon = lab.icon;
            return (
              <div
                key={lab.id}
                className={`card-elevated p-6 transition-all ${
                  lab.available
                    ? 'hover:shadow-soft-lg hover:-translate-y-0.5 cursor-pointer'
                    : 'opacity-60'
                }`}
              >
                <div className="flex items-start gap-4">
                  <div className={`w-12 h-12 rounded-xl ${lab.color} flex items-center justify-center shrink-0`}>
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-bold text-base mb-1">
                      {lab.title[langKey]}
                    </h3>
                    <p className="text-sm text-muted-foreground mb-3">
                      {lab.description[langKey]}
                    </p>
                    {lab.available ? (
                      <Link
                        href={`/lab/${lab.id}`}
                        className="btn-pill btn-primary inline-flex items-center text-sm py-2 px-4"
                      >
                        {t('lab.start')}
                      </Link>
                    ) : (
                      <span className="inline-flex items-center text-sm text-muted-foreground bg-muted rounded-full px-4 py-2">
                        {locale === 'kz' ? 'Жақында' : 'Скоро'}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </main>
    </div>
  );
}
