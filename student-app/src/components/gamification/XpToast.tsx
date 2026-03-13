'use client';

import { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { useGamificationStore } from '@/stores/gamification-store';

export function XpToast() {
  const t = useTranslations('gamification');
  const { xpToast, hideXpToast } = useGamificationStore();
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (xpToast) {
      setVisible(true);
      const timer = setTimeout(() => {
        setVisible(false);
        setTimeout(hideXpToast, 300);
      }, 2500);
      return () => clearTimeout(timer);
    }
  }, [xpToast, hideXpToast]);

  if (!xpToast) return null;

  const isLevelUp = !!xpToast.levelUp;

  return (
    <div
      className={`fixed right-4 top-4 z-[100] transition-all duration-300 ${
        visible ? 'translate-y-0 opacity-100' : '-translate-y-4 opacity-0'
      }`}
    >
      <div
        className={`rounded-xl px-4 py-3 shadow-lg ${
          isLevelUp
            ? 'bg-gradient-to-r from-violet-500 to-blue-500 text-white'
            : 'bg-emerald-500 text-white'
        }`}
      >
        <p className="text-sm font-bold">
          {isLevelUp
            ? t('levelUp', { level: xpToast.levelUp! })
            : t('xpAwarded', { amount: xpToast.amount })}
        </p>
        {isLevelUp && (
          <p className="text-xs opacity-90">
            {t('xpAwarded', { amount: xpToast.amount })}
          </p>
        )}
      </div>
    </div>
  );
}
