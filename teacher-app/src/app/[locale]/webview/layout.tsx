'use client';

import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';

function TokenExtractor({ children }: { children: React.ReactNode }) {
  const searchParams = useSearchParams();

  // Extract token SYNCHRONOUSLY before children render/mount.
  // Writing here guarantees children always see the fresh URL token on mount.
  if (typeof window !== 'undefined') {
    const token = searchParams.get('token');
    if (token) {
      localStorage.setItem('ai_mentor_teacher_access_token', token);
    }
  }

  return <>{children}</>;
}

export default function WebViewLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      <Suspense>
        <TokenExtractor>{children}</TokenExtractor>
      </Suspense>
    </div>
  );
}
