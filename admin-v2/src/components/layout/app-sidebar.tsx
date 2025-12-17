'use client';

import { useTranslations } from 'next-intl';
import { usePathname } from 'next/navigation';
import { Link } from '@/i18n/navigation';
import { useAuth } from '@/providers/auth-provider';
import { cn } from '@/lib/utils';
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from '@/components/ui/sidebar';
import {
  LayoutDashboard,
  School,
  BookOpen,
  FileQuestion,
  Users,
  GraduationCap,
  UserCircle,
  FolderOpen,
  Settings,
  Scale,
  Target,
} from 'lucide-react';

interface NavItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  roles: ('super_admin' | 'admin')[];
}

const navItems: NavItem[] = [
  {
    title: 'dashboard',
    href: '/',
    icon: LayoutDashboard,
    roles: ['super_admin', 'admin'],
  },
  // SUPER_ADMIN items
  {
    title: 'schools',
    href: '/schools',
    icon: School,
    roles: ['super_admin'],
  },
  {
    title: 'textbooks',
    href: '/textbooks',
    icon: BookOpen,
    roles: ['super_admin'],
  },
  {
    title: 'tests',
    href: '/tests',
    icon: FileQuestion,
    roles: ['super_admin'],
  },
  {
    title: 'gosoFrameworks',
    href: '/goso/frameworks',
    icon: Scale,
    roles: ['super_admin'],
  },
  {
    title: 'learningOutcomes',
    href: '/goso/outcomes',
    icon: Target,
    roles: ['super_admin'],
  },
  // School ADMIN items
  {
    title: 'students',
    href: '/students',
    icon: Users,
    roles: ['admin'],
  },
  {
    title: 'teachers',
    href: '/teachers',
    icon: GraduationCap,
    roles: ['admin'],
  },
  {
    title: 'parents',
    href: '/parents',
    icon: UserCircle,
    roles: ['admin'],
  },
  {
    title: 'classes',
    href: '/classes',
    icon: FolderOpen,
    roles: ['admin'],
  },
  {
    title: 'textbookLibrary',
    href: '/school-textbooks',
    icon: BookOpen,
    roles: ['admin'],
  },
  {
    title: 'testLibrary',
    href: '/school-tests',
    icon: FileQuestion,
    roles: ['admin'],
  },
  {
    title: 'settings',
    href: '/settings',
    icon: Settings,
    roles: ['admin'],
  },
];

export function AppSidebar() {
  const t = useTranslations('nav');
  const pathname = usePathname();
  const { user } = useAuth();

  // Get locale from pathname for comparison
  const locale = pathname.split('/')[1] || 'ru';

  const filteredItems = navItems.filter(
    (item) => user && item.roles.includes(user.role as 'super_admin' | 'admin')
  );

  const isActive = (href: string) => {
    const fullPath = `/${locale}${href === '/' ? '' : href}`;
    if (href === '/') {
      return pathname === `/${locale}` || pathname === `/${locale}/`;
    }
    return pathname.startsWith(fullPath);
  };

  return (
    <Sidebar>
      <SidebarHeader className="border-b px-6 py-4">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <GraduationCap className="h-6 w-6" />
          <span>AI Mentor</span>
        </Link>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Меню</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {filteredItems.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);

                return (
                  <SidebarMenuItem key={item.href}>
                    <SidebarMenuButton asChild isActive={active}>
                      <Link href={item.href}>
                        <Icon className="h-4 w-4" />
                        <span>{t(item.title)}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarRail />
    </Sidebar>
  );
}
