'use client';

import { useTranslations } from 'next-intl';
import { X, Clock, Hexagon, Link2, Lightbulb } from 'lucide-react';
import type { MoleculeData } from './molecules-data';

interface MoleculeInfoProps {
  molecule: MoleculeData;
  locale: string;
  onClose: () => void;
}

export function MoleculeInfo({ molecule, locale, onClose }: MoleculeInfoProps) {
  const t = useTranslations();
  const isKk = locale === 'kz';

  const name = isKk ? molecule.name_kk : molecule.name;
  const description = isKk ? molecule.description_kk : molecule.description;
  const bondType = isKk ? molecule.bondType_kk : molecule.bondType;
  const geometry = isKk ? molecule.geometry_kk : molecule.geometry;
  const facts = isKk ? molecule.facts_kk : molecule.facts;

  return (
    <div className="absolute top-0 right-0 bottom-0 z-[1001] w-80 max-w-[85vw] bg-card shadow-soft-lg border-l border-border flex flex-col animate-in slide-in-from-right">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex items-center gap-2">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: molecule.color }}
          />
          <h2 className="font-bold text-sm">{t('chemistry.molecule')}</h2>
        </div>
        <button
          onClick={onClose}
          className="w-8 h-8 rounded-lg hover:bg-muted flex items-center justify-center"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <div>
          <h3 className="text-lg font-bold">{name}</h3>
          <p className="text-xl font-mono text-primary mt-0.5">{molecule.formula}</p>
          <div className="flex items-center gap-1.5 mt-1 text-sm text-muted-foreground">
            <Clock className="w-3.5 h-3.5" />
            {molecule.molarMass}
          </div>
        </div>

        <p className="text-sm leading-relaxed">{description}</p>

        {/* Geometry */}
        <div className="card-flat p-3 space-y-1.5">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase">
            <Hexagon className="w-3.5 h-3.5" />
            {t('chemistry.geometry')}
          </div>
          <p className="text-sm">{geometry}</p>
        </div>

        {/* Bond type */}
        <div className="card-flat p-3 space-y-1.5">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase">
            <Link2 className="w-3.5 h-3.5" />
            {t('chemistry.bondType')}
          </div>
          <p className="text-sm">{bondType}</p>
        </div>

        {/* Facts */}
        {facts.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase">
              <Lightbulb className="w-3.5 h-3.5" />
              {t('chemistry.facts')}
            </div>
            <ul className="space-y-1.5">
              {facts.map((fact, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <span
                    className="w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0"
                    style={{ backgroundColor: molecule.color }}
                  />
                  {fact}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
