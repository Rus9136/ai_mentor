'use client';

import { AppSidebar } from '@/components/layout/AppSidebar';
import { TopBar } from '@/components/layout/TopBar';
import { MobileBottomNav } from '@/components/layout/MobileBottomNav';

interface AppLayoutProps {
  children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="flex h-screen bg-background">
      <AppSidebar />
      <div className="flex flex-1 flex-col min-w-0 h-full">
        <TopBar />
        <main className="flex-1 min-h-0 overflow-y-auto pb-20 md:pb-0">{children}</main>
      </div>
      <MobileBottomNav />
    </div>
  );
}
