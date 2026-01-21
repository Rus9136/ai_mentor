'use client';

import { useState } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { useRouter, usePathname } from '@/i18n/routing';
import { Globe, LogOut, Trash2, ChevronRight, UserPlus } from 'lucide-react';
import { useAuth } from '@/providers/auth-provider';
import { useJoinRequestStatus } from '@/lib/hooks/use-join-request';
import { JoinClassModal } from './JoinClassModal';
import { JoinRequestStatus } from './JoinRequestStatus';

export function SettingsSection() {
  const t = useTranslations('profile');
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();
  const { logout, deleteAccount } = useAuth();
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showJoinClassModal, setShowJoinClassModal] = useState(false);

  const { data: joinRequestStatus, refetch: refetchJoinStatus } = useJoinRequestStatus();

  const handleLanguageChange = (newLocale: 'ru' | 'kz') => {
    if (newLocale !== locale) {
      router.replace(pathname, { locale: newLocale });
    }
  };

  const handleLogout = () => {
    logout();
  };

  const handleDeleteAccount = async () => {
    setIsDeleting(true);
    await deleteAccount();
    setIsDeleting(false);
  };

  return (
    <div className="space-y-3">
      {/* Join Class Section */}
      {joinRequestStatus?.has_request ? (
        <JoinRequestStatus
          status={joinRequestStatus}
          onTryAgain={() => setShowJoinClassModal(true)}
        />
      ) : (
        <button
          onClick={() => setShowJoinClassModal(true)}
          className="card-flat flex w-full items-center justify-between p-4 text-left transition-colors hover:bg-muted/50"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
              <UserPlus className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="font-medium text-foreground">{t('joinClass.button')}</p>
              <p className="text-sm text-muted-foreground">{t('joinClass.description')}</p>
            </div>
          </div>
          <ChevronRight className="h-5 w-5 text-muted-foreground" />
        </button>
      )}

      {/* Join Class Modal */}
      <JoinClassModal
        isOpen={showJoinClassModal}
        onClose={() => setShowJoinClassModal(false)}
        onSuccess={() => refetchJoinStatus()}
      />

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
                {locale === 'ru' ? t('language.ru') : t('language.kz')}
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
              onClick={() => handleLanguageChange('kz')}
              className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
                locale === 'kz'
                  ? 'bg-primary text-white'
                  : 'bg-muted text-muted-foreground hover:bg-muted/80'
              }`}
            >
              KZ
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

      {/* Delete Account Button */}
      {!showDeleteConfirm ? (
        <button
          onClick={() => setShowDeleteConfirm(true)}
          className="card-flat flex w-full items-center justify-between p-4 text-left transition-colors hover:bg-muted/50"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-100">
              <Trash2 className="h-5 w-5 text-red-500" />
            </div>
            <span className="font-medium text-red-600">{t('deleteAccount')}</span>
          </div>
          <ChevronRight className="h-5 w-5 text-muted-foreground" />
        </button>
      ) : (
        <div className="card-elevated space-y-3 p-4">
          <p className="text-center font-medium text-foreground">{t('confirmDelete')}</p>
          <p className="text-center text-sm text-muted-foreground">{t('deleteWarning')}</p>
          <div className="flex gap-3">
            <button
              onClick={() => setShowDeleteConfirm(false)}
              disabled={isDeleting}
              className="flex-1 rounded-full bg-muted py-2.5 font-medium text-muted-foreground transition-colors hover:bg-muted/80 disabled:opacity-50"
            >
              {t('cancel')}
            </button>
            <button
              onClick={handleDeleteAccount}
              disabled={isDeleting}
              className="flex-1 rounded-full bg-red-500 py-2.5 font-medium text-white transition-colors hover:bg-red-600 disabled:opacity-50"
            >
              {isDeleting ? t('deleting') : t('deleteAccount')}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
