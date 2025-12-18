'use client';

import { useEffect, useRef, useState } from 'react';
import { useTranslations } from 'next-intl';
import { Loader2 } from 'lucide-react';

interface GoogleSignInButtonProps {
  onSuccess: (idToken: string) => void;
  onError?: (error: string) => void;
}

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (response: { credential: string }) => void;
            auto_select?: boolean;
            itp_support?: boolean;
          }) => void;
          renderButton: (
            element: HTMLElement,
            options: {
              theme?: 'outline' | 'filled_blue' | 'filled_black';
              size?: 'large' | 'medium' | 'small';
              text?: 'signin_with' | 'signup_with' | 'continue_with' | 'signin';
              shape?: 'rectangular' | 'pill' | 'circle' | 'square';
              logo_alignment?: 'left' | 'center';
              width?: string | number;
              locale?: string;
            }
          ) => void;
          prompt: () => void;
        };
      };
    };
  }
}

export function GoogleSignInButton({
  onSuccess,
  onError,
}: GoogleSignInButtonProps) {
  const t = useTranslations('auth.login');
  const buttonRef = useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [scriptLoaded, setScriptLoaded] = useState(false);

  useEffect(() => {
    // Load Google Identity Services script
    console.log('[GoogleSignIn] Loading script...');
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => {
      console.log('[GoogleSignIn] Script loaded successfully');
      setScriptLoaded(true);
    };
    script.onerror = (e) => {
      console.error('[GoogleSignIn] Script load error:', e);
      setIsLoading(false);
      onError?.('Failed to load Google Sign-In');
    };
    document.head.appendChild(script);

    return () => {
      if (script.parentNode) {
        document.head.removeChild(script);
      }
    };
  }, [onError]);

  useEffect(() => {
    console.log('[GoogleSignIn] Init effect - scriptLoaded:', scriptLoaded, 'buttonRef:', !!buttonRef.current);
    if (!scriptLoaded || !buttonRef.current) return;

    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
    console.log('[GoogleSignIn] Client ID:', clientId ? clientId.substring(0, 20) + '...' : 'NOT SET');

    if (!clientId) {
      setIsLoading(false);
      onError?.('Google Client ID not configured');
      return;
    }

    try {
      console.log('[GoogleSignIn] window.google:', !!window.google);
      window.google?.accounts.id.initialize({
        client_id: clientId,
        callback: (response) => {
          console.log('[GoogleSignIn] Callback received, has credential:', !!response.credential);
          if (response.credential) {
            onSuccess(response.credential);
          }
        },
        auto_select: false,
        itp_support: true,
      });

      window.google?.accounts.id.renderButton(buttonRef.current, {
        theme: 'outline',
        size: 'large',
        text: 'continue_with',
        shape: 'rectangular',
        width: 280,
      });

      console.log('[GoogleSignIn] Button rendered, setting isLoading=false');
      setIsLoading(false);
    } catch (err) {
      console.error('[GoogleSignIn] Init error:', err);
      setIsLoading(false);
      onError?.('Failed to initialize Google Sign-In');
    }
  }, [scriptLoaded, onSuccess, onError]);

  return (
    <div className="flex justify-center">
      {isLoading && (
        <div className="flex h-10 w-[280px] items-center justify-center rounded-md border bg-white">
          <Loader2 className="h-5 w-5 animate-spin text-gray-500" />
          <span className="ml-2 text-sm text-gray-500">{t('loading')}</span>
        </div>
      )}
      <div
        ref={buttonRef}
        className={isLoading ? 'hidden' : ''}
      />
    </div>
  );
}
