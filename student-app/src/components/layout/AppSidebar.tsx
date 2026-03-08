'use client';

import { useTranslations } from 'next-intl';
import { usePathname } from 'next/navigation';
import { Link } from '@/i18n/routing';
import {
  Home,
  BookOpen,
  FileCheck,
  ClipboardList,
  GraduationCap,
  User,
} from 'lucide-react';
import { SidebarChapterProgress } from './SidebarChapterProgress';
import { useChapterParagraphs, useParagraphNavigation } from '@/lib/hooks/use-textbooks';

export function AppSidebar() {
  const t = useTranslations('navigation');
  const pathname = usePathname();

  // Detect if we're on a paragraph page
  const paragraphMatch = pathname.match(/\/paragraphs\/(\d+)/);
  const paragraphId = paragraphMatch ? parseInt(paragraphMatch[1], 10) : null;

  return (
    <aside className="hidden md:flex w-[260px] flex-col flex-shrink-0 bg-[#FFF8F2] border-r border-[#EDE8E3]">
      {/* Logo */}
      <div className="flex items-center gap-[10px] px-5 py-4 border-b border-[#EDE8E3]">
        <Link href="/home" className="flex items-center gap-[10px]">
          <div className="flex h-9 w-9 items-center justify-center rounded-[10px] bg-primary">
            <GraduationCap className="h-[18px] w-[18px] text-white" />
          </div>
          <span className="text-base font-extrabold text-foreground tracking-tight">
            AI Mentor
          </span>
        </Link>
      </div>

      {/* Content: either chapter progress or normal nav */}
      {paragraphId ? (
        <SidebarChapterContent paragraphId={paragraphId} />
      ) : (
        <DefaultNav />
      )}
    </aside>
  );
}

// Separate component to allow hooks usage conditionally
function SidebarChapterContent({ paragraphId }: { paragraphId: number }) {
  const { data: navigation } = useParagraphNavigation(paragraphId);
  const { data: chapterParagraphs } = useChapterParagraphs(navigation?.chapter_id);

  if (!navigation || !chapterParagraphs) {
    return <DefaultNav />;
  }

  return (
    <SidebarChapterProgress
      paragraphs={chapterParagraphs}
      currentParagraphId={paragraphId}
      chapterTitle={navigation.chapter_title}
      chapterNumber={navigation.chapter_number}
      chapterId={navigation.chapter_id}
      textbookTitle={navigation.textbook_title}
    />
  );
}

function DefaultNav() {
  const t = useTranslations('navigation');
  const pathname = usePathname();

  const navItems = [
    { href: '/home', icon: Home, label: t('home') },
    { href: '/subjects', icon: BookOpen, label: t('subjects') },
    { href: '/tests', icon: FileCheck, label: t('tests') },
    { href: '/homework', icon: ClipboardList, label: t('homework') },
  ];

  const isActive = (href: string) => {
    if (href === '/home') return pathname.includes('/home') && !pathname.includes('/homework');
    return pathname.includes(href);
  };

  return (
    <nav className="flex-1 overflow-y-auto px-[10px] py-3">
      <div className="mb-5">
        <div className="px-[10px] mb-1.5 text-[10px] font-bold text-[#A09080] uppercase tracking-[1px]">
          {t('menu')}
        </div>
        <ul className="space-y-0.5">
          {navItems.map((item) => (
            <li key={item.href}>
              <Link
                href={item.href}
                className={`flex items-center gap-[10px] px-[10px] py-[9px] rounded-[10px] text-[13px] font-semibold transition-all ${
                  isActive(item.href)
                    ? 'bg-primary text-white'
                    : 'text-[#6B5B4E] hover:bg-[#F0E8E0] hover:text-foreground'
                }`}
              >
                <item.icon className={`h-4 w-4 ${isActive(item.href) ? 'text-white' : ''}`} />
                {item.label}
              </Link>
            </li>
          ))}
        </ul>
      </div>

      {/* Profile */}
      <div>
        <div className="px-[10px] mb-1.5 text-[10px] font-bold text-[#A09080] uppercase tracking-[1px]">
          {t('profile')}
        </div>
        <ul className="space-y-0.5">
          <li>
            <Link
              href="/profile"
              className={`flex items-center gap-[10px] px-[10px] py-[9px] rounded-[10px] text-[13px] font-semibold transition-all ${
                pathname.includes('/profile')
                  ? 'bg-primary text-white'
                  : 'text-[#6B5B4E] hover:bg-[#F0E8E0] hover:text-foreground'
              }`}
            >
              <User className={`h-4 w-4 ${pathname.includes('/profile') ? 'text-white' : ''}`} />
              {t('profile')}
            </Link>
          </li>
        </ul>
      </div>
    </nav>
  );
}
