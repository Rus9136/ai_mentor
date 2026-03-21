'use client';

import { useState } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { ArrowLeft, Info, RotateCw, Eye } from 'lucide-react';
import { Link } from '@/i18n/routing';
import { MOLECULES } from './molecules-data';
import { MoleculeInfo } from './MoleculeInfo';
import type { ViewStyle } from './MoleculeViewer';
import dynamic from 'next/dynamic';

const MoleculeViewer = dynamic(
  () => import('./MoleculeViewer').then((mod) => ({ default: mod.MoleculeViewer })),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-full bg-white">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    ),
  }
);

const STYLE_OPTIONS: { value: ViewStyle; label: string; label_kk: string }[] = [
  { value: 'ballAndStick', label: 'Шарики и палочки', label_kk: 'Шарлар мен таяқшалар' },
  { value: 'stick', label: 'Палочки', label_kk: 'Таяқшалар' },
  { value: 'sphere', label: 'Сферы (Ван-дер-Ваальс)', label_kk: 'Сфералар' },
  { value: 'line', label: 'Каркас', label_kk: 'Қаңқа' },
];

export default function ChemistryLab() {
  const t = useTranslations();
  const locale = useLocale();
  const isKk = locale === 'kz';

  const [selectedMolecule, setSelectedMolecule] = useState(MOLECULES[0]);
  const [viewStyle, setViewStyle] = useState<ViewStyle>('ballAndStick');
  const [spinning, setSpinning] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showIntro, setShowIntro] = useState(true);

  return (
    <div className="h-screen flex flex-col relative bg-white">
      {/* Top bar */}
      <div className="absolute top-0 left-0 right-0 z-[1000] flex items-center gap-2 p-3">
        <Link
          href="/"
          className="w-10 h-10 rounded-xl bg-card/90 backdrop-blur-sm shadow-soft flex items-center justify-center hover:bg-card transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div className="flex-1 bg-card/90 backdrop-blur-sm rounded-xl shadow-soft px-4 py-2">
          <h1 className="font-bold text-sm">{t('chemistry.title')}</h1>
          <p className="text-xs text-muted-foreground">
            {isKk ? selectedMolecule.name_kk : selectedMolecule.name} · {selectedMolecule.formula}
          </p>
        </div>
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="w-10 h-10 rounded-xl bg-card/90 backdrop-blur-sm shadow-soft flex items-center justify-center hover:bg-card transition-colors"
        >
          <Info className="w-5 h-5" />
        </button>
      </div>

      {/* 3D Viewer */}
      <div className="flex-1 relative">
        <MoleculeViewer
          cid={selectedMolecule.cid}
          viewStyle={viewStyle}
          spinning={spinning}
        />

        {/* Intro overlay */}
        {showIntro && (
          <div className="absolute inset-0 z-[999] bg-black/40 flex items-center justify-center p-4">
            <div className="card-elevated p-6 max-w-sm text-center">
              <div className="w-16 h-16 rounded-2xl bg-blue-500 flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">{'\u269B\uFE0F'}</span>
              </div>
              <h2 className="text-lg font-bold mb-2">{t('chemistry.explore')}</h2>
              <p className="text-sm text-muted-foreground mb-4">
                {t('chemistry.exploreDescription')}
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

      {/* Controls bar */}
      <div className="absolute bottom-[88px] left-3 right-3 z-[1000]">
        <div className="bg-card/95 backdrop-blur-sm rounded-xl shadow-soft px-3 py-2 flex items-center gap-2 overflow-x-auto">
          {/* View style buttons */}
          <div className="flex items-center gap-1 mr-2">
            <Eye className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
            {STYLE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setViewStyle(opt.value)}
                className={`text-[11px] px-2.5 py-1 rounded-full whitespace-nowrap transition-colors ${
                  viewStyle === opt.value
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:bg-muted/80'
                }`}
              >
                {isKk ? opt.label_kk : opt.label}
              </button>
            ))}
          </div>

          {/* Spin toggle */}
          <button
            onClick={() => setSpinning(!spinning)}
            className={`flex items-center gap-1 text-[11px] px-2.5 py-1 rounded-full whitespace-nowrap transition-colors flex-shrink-0 ${
              spinning
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-muted-foreground'
            }`}
          >
            <RotateCw className="w-3 h-3" />
            {isKk ? 'Айналу' : 'Вращение'}
          </button>
        </div>
      </div>

      {/* Molecule selector */}
      <div className="absolute bottom-0 left-0 right-0 z-[1000]">
        <div className="bg-card/95 backdrop-blur-sm border-t border-border px-3 py-2.5 pb-[env(safe-area-inset-bottom,0.75rem)]">
          <div className="flex items-center gap-2 overflow-x-auto pb-1">
            {MOLECULES.map((mol) => (
              <button
                key={mol.id}
                onClick={() => setSelectedMolecule(mol)}
                className={`flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-xl whitespace-nowrap transition-all flex-shrink-0 ${
                  selectedMolecule.id === mol.id
                    ? 'bg-primary/10 scale-105'
                    : 'hover:bg-muted'
                }`}
              >
                <span
                  className={`w-3 h-3 rounded-full border-2 transition-all ${
                    selectedMolecule.id === mol.id
                      ? 'border-white shadow-md scale-110'
                      : 'border-transparent'
                  }`}
                  style={{ backgroundColor: mol.color }}
                />
                <span className="text-[10px] font-mono font-bold">{mol.formula}</span>
                <span className="text-[9px] text-muted-foreground">
                  {isKk ? mol.name_kk : mol.name}
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Info Sidebar */}
      {sidebarOpen && (
        <MoleculeInfo
          molecule={selectedMolecule}
          locale={locale}
          onClose={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}
