'use client';

import { use, useEffect } from 'react';
import { useAuth } from '@/providers/auth-provider';
import dynamic from 'next/dynamic';

const HistoryLab = dynamic(() => import('@/components/history/HistoryLab'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-screen">
      <div className="text-muted-foreground animate-pulse">Loading...</div>
    </div>
  ),
});

interface WebViewLabPageProps {
  params: Promise<{ labId: string }>;
}

/**
 * WebView version of the lab page — no header/navigation.
 * JWT token is passed via URL query parameter: ?token=xxx
 * Token is extracted and stored by AuthProvider.
 */
export default function WebViewLabPage({ params }: WebViewLabPageProps) {
  const { labId } = use(params);
  const { user, isLoading } = useAuth();

  // In WebView, suppress any redirects
  useEffect(() => {
    if (typeof window !== 'undefined') {
      document.body.style.overflow = 'hidden';
    }
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-muted-foreground animate-pulse">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-destructive">Authentication required</div>
      </div>
    );
  }

  const labIdNum = parseInt(labId);
  if (labIdNum !== 1) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-muted-foreground">Lab not found</div>
      </div>
    );
  }

  return <HistoryLab />;
}
