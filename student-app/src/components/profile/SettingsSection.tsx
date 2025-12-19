'use client';

import { useState } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { useRouter, usePathname } from '@/i18n/routing';
import { Globe, LogOut, ChevronRight } from 'lucide-react';
import { useAuth } from '@/providers/auth-provider';

export function SettingsSection() {
  const t = useTranslations('profile');
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();
  const { logout } = useAuth();
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  const handleLanguageChange = (newLocale: 'ru' | 'kk') => {
    if (newLocale !== locale) {
      router.replace(pathname, { locale: newLocale });
    }
  };

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="space-y-3">
      {/* Language Switcher */}
      <div className="card-flat overflow-hidden">
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
              <Globe className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="font-medium text-foreground">{t('language.title')}</p>
              <p className="text-sm text-muted-foreground">
                {locale === 'ru' ? t('language.ru') : t('language.kk')}
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => handleLanguageChange('ru')}
              className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
                locale === 'ru'
                  ? 'bg-primary text-white'
                  : 'bg-muted text-muted-foreground hover:bg-muted/80'
              }`}
            >
              RU
            </button>
            <button
              onClick={() => handleLanguageChange('kk')}
              className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
                locale === 'kk'
                  ? 'bg-primary text-white'
                  : 'bg-muted text-muted-foreground hover:bg-muted/80'
              }`}
            >
              KK
            </button>
          </div>
        </div>
      </div>

      {/* Logout Button */}
      {!showLogoutConfirm ? (
        <button
          onClick={() => setShowLogoutConfirm(true)}
          className="card-flat flex w-full items-center justify-between p-4 text-left transition-colors hover:bg-muted/50"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-100">
              <LogOut className="h-5 w-5 text-red-500" />
            </div>
            <span className="font-medium text-red-600">{t('logout')}</span>
          </div>
          <ChevronRight className="h-5 w-5 text-muted-foreground" />
        </button>
      ) : (
        <div className="card-elevated space-y-3 p-4">
          <p className="text-center font-medium text-foreground">{t('confirmLogout')}</p>
          <div className="flex gap-3">
            <button
              onClick={() => setShowLogoutConfirm(false)}
              className="flex-1 rounded-full bg-muted py-2.5 font-medium text-muted-foreground transition-colors hover:bg-muted/80"
            >
              {t('cancel')}
            </button>
            <button
              onClick={handleLogout}
              className="flex-1 rounded-full bg-red-500 py-2.5 font-medium text-white transition-colors hover:bg-red-600"
            >
              {t('logout')}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
