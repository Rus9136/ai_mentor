'use client';

import { useTranslations } from 'next-intl';
import { usePathname } from 'next/navigation';
import { Link } from '@/i18n/routing';
import {
  Home,
  BookOpen,
  User,
  FileCheck,
  ClipboardList,
} from 'lucide-react';

export function MobileBottomNav() {
  const t = useTranslations('navigation');
  const pathname = usePathname();

  const navItems = [
    { href: '/home', icon: Home, label: t('home') },
    { href: '/subjects', icon: BookOpen, label: t('subjects') },
    { href: '/tests', icon: FileCheck, label: t('tests') },
    { href: '/homework', icon: ClipboardList, label: t('homework') },
    { href: '/profile', icon: User, label: t('profile') },
  ];

  const isActive = (href: string) => {
    if (href === '/home') return pathname.includes('/home');
    return pathname.includes(href);
  };

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 border-t border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 md:hidden">
      <div className="flex h-16 items-center justify-around">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`flex flex-1 flex-col items-center gap-1 py-2 ${
              isActive(item.href)
                ? 'text-primary'
                : 'text-muted-foreground'
            }`}
          >
            <item.icon className="h-5 w-5" />
            <span className="text-xs font-medium">{item.label}</span>
          </Link>
        ))}
      </div>
    </nav>
  );
}
