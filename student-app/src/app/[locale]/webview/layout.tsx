'use client';

import { useSearchParams } from 'next/navigation';
import { useEffect } from 'react';

export default function WebViewLayout({ children }: { children: React.ReactNode }) {
  const searchParams = useSearchParams();

  useEffect(() => {
    const token = searchParams.get('token');
    if (token) {
      localStorage.setItem('ai_mentor_access_token', token);
    }
  }, [searchParams]);

  return (
    <div className="min-h-dvh bg-background">
      {children}
    </div>
  );
}
