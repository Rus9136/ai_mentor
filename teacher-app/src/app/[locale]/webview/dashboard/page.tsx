'use client';

import { useEffect } from 'react';
import { useRouter } from '@/i18n/routing';
import { useAuth } from '@/providers/auth-provider';

/**
 * WebView entry point for the mobile app.
 * Accepts ?token=JWT, saves it via layout's TokenExtractor,
 * then redirects to the main dashboard.
 */
export default function WebViewDashboardPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;

    if (user) {
      router.replace('/');
    }
    // If no user and not loading — token was invalid.
    // Stay on this page; mobile app will handle re-auth.
  }, [user, isLoading, router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
    </div>
  );
}
