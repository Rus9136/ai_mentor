'use client';

import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';

function TokenExtractor({ children }: { children: React.ReactNode }) {
  const searchParams = useSearchParams();

  // Extract token SYNCHRONOUSLY before children render/mount.
  // useEffect runs parent-AFTER-children, so children's useEffect (e.g. auto-join)
  // would fire with a stale localStorage token. Writing here guarantees children
  // always see the fresh URL token on mount.
  if (typeof window !== 'undefined') {
    const token = searchParams.get('token');
    if (token) {
      localStorage.setItem('ai_mentor_access_token', token);
    }
  }

  return <>{children}</>;
}

export default function WebViewLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-dvh bg-background">
      <Suspense>
        <TokenExtractor>{children}</TokenExtractor>
      </Suspense>
    </div>
  );
}
