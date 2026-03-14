'use client';

import { useSearchParams } from 'next/navigation';
import { useEffect, Suspense } from 'react';

function TokenExtractor({ children }: { children: React.ReactNode }) {
  const searchParams = useSearchParams();

  useEffect(() => {
    const token = searchParams.get('token');
    if (token) {
      localStorage.setItem('ai_mentor_access_token', token);
    }
  }, [searchParams]);

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
