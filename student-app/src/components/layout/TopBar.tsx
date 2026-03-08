'use client';

import { Link } from '@/i18n/routing';
import { useAuth } from '@/providers/auth-provider';
import { GraduationCap, LogOut } from 'lucide-react';
import { useTranslations } from 'next-intl';

interface TopBarProps {
  children?: React.ReactNode;
  actions?: React.ReactNode;
}

export function TopBar({ children, actions }: TopBarProps) {
  const { user, logout } = useAuth();
  const t = useTranslations('navigation');

  return (
    <>
      {/* Desktop TopBar */}
      <header className="hidden md:flex h-14 items-center px-6 gap-4 bg-[#FFF8F2] border-b border-[#EDE8E3] flex-shrink-0">
        {/* Left: breadcrumbs slot */}
        <div className="flex items-center gap-1.5 text-[13px] font-semibold text-[#A09080] flex-1 min-w-0">
          {children}
        </div>

        {/* Center/Right: custom actions (ViewToggle, etc.) */}
        {actions && <div className="flex items-center gap-2">{actions}</div>}

        {/* Avatar + logout */}
        <div className="flex items-center gap-3 ml-2">
          {user?.avatar_url ? (
            <img
              src={user.avatar_url}
              alt="Avatar"
              className="h-8 w-8 rounded-full ring-2 ring-border"
            />
          ) : (
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-xs font-extrabold text-white">
              {user?.first_name?.[0]}
              {user?.last_name?.[0]}
            </div>
          )}
          <button
            onClick={logout}
            className="p-2 rounded-full text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
            title={t('logout')}
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </header>

      {/* Mobile Header */}
      <header className="flex md:hidden h-14 items-center justify-between px-4 border-b border-border/40 bg-background/95 backdrop-blur sticky top-0 z-50">
        <Link href="/home" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
            <GraduationCap className="h-4 w-4 text-white" />
          </div>
          <span className="font-bold text-foreground">AI Mentor</span>
        </Link>

        <div className="flex items-center gap-2">
          {user?.avatar_url ? (
            <img
              src={user.avatar_url}
              alt="Avatar"
              className="h-8 w-8 rounded-full ring-2 ring-border"
            />
          ) : (
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
              {user?.first_name?.[0]}
              {user?.last_name?.[0]}
            </div>
          )}
        </div>
      </header>
    </>
  );
}
