'use client';

import { useState, useEffect } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { ArrowLeft, Info } from 'lucide-react';
import { Link } from '@/i18n/routing';
import { useLabStore } from '@/stores/lab-store';
import { Timeline } from './Timeline';
import { EpochInfo } from './EpochInfo';
import { EPOCHS } from './epochs-data';
import dynamic from 'next/dynamic';

const HistoryMap = dynamic(
  () => import('./HistoryMap').then((mod) => ({ default: mod.HistoryMap })),
  { ssr: false }
);

export default function HistoryLab() {
  const t = useTranslations();
  const locale = useLocale();
  const { currentEpochId, setCurrentEpochId, sidebarOpen, setSidebarOpen } = useLabStore();
  const [showIntro, setShowIntro] = useState(true);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [territories, setTerritories] = useState<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [markers, setMarkers] = useState<any>(null);

  const currentEpoch = EPOCHS.find((e) => e.id === currentEpochId) || EPOCHS[0];
  const isKk = locale === 'kz';

  // Load GeoJSON data on mount
  useEffect(() => {
    fetch('/data/history/territories.geojson')
      .then((res) => res.json())
      .then(setTerritories)
      .catch(console.error);

    fetch('/data/history/markers.geojson')
      .then((res) => res.json())
      .then(setMarkers)
      .catch(console.error);
  }, []);

  return (
    <div className="h-screen flex flex-col relative">
      {/* Top bar */}
      <div className="absolute top-0 left-0 right-0 z-[1000] flex items-center gap-2 p-3">
        <Link
          href="/"
          className="w-10 h-10 rounded-xl bg-card/90 backdrop-blur-sm shadow-soft flex items-center justify-center hover:bg-card transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div className="flex-1 bg-card/90 backdrop-blur-sm rounded-xl shadow-soft px-4 py-2">
          <h1 className="font-bold text-sm">{t('history.title')}</h1>
          <p className="text-xs text-muted-foreground">
            {isKk ? currentEpoch.name_kk : currentEpoch.name} · {currentEpoch.period}
          </p>
        </div>
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="w-10 h-10 rounded-xl bg-card/90 backdrop-blur-sm shadow-soft flex items-center justify-center hover:bg-card transition-colors"
        >
          <Info className="w-5 h-5" />
        </button>
      </div>

      {/* Map */}
      <div className="flex-1 relative">
        <HistoryMap
          epoch={currentEpoch}
          territories={territories}
          markers={markers}
          locale={locale}
        />

        {/* Intro overlay */}
        {showIntro && (
          <div className="absolute inset-0 z-[999] bg-black/40 flex items-center justify-center p-4">
            <div className="card-elevated p-6 max-w-sm text-center">
              <div className="w-16 h-16 rounded-2xl bg-amber-500 flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">{'\uD83D\uDDFA\uFE0F'}</span>
              </div>
              <h2 className="text-lg font-bold mb-2">{t('history.exploreMap')}</h2>
              <p className="text-sm text-muted-foreground mb-4">
                {t('history.exploreMapDescription')}
              </p>
              <button
                onClick={() => setShowIntro(false)}
                className="btn-pill btn-primary text-sm py-2 px-6"
              >
                {t('lab.start')}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Timeline */}
      <div className="absolute bottom-0 left-0 right-0 z-[1000]">
        <Timeline
          epochs={EPOCHS}
          currentEpochId={currentEpoch.id}
          onEpochChange={(id) => setCurrentEpochId(id)}
          locale={locale}
        />
      </div>

      {/* Epoch Info Sidebar */}
      {sidebarOpen && (
        <EpochInfo
          epoch={currentEpoch}
          locale={locale}
          onClose={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}
