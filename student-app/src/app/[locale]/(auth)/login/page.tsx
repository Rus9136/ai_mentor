'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { useAuth } from '@/providers/auth-provider';
import { GoogleSignInButton } from '@/components/auth/google-signin-button';
import { useRouter } from '@/i18n/routing';
import { Loader2, BookOpen, Sparkles, GraduationCap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function LoginPage() {
  const t = useTranslations('auth.login');
  const { login, loginWithPassword, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Email/Password form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleGoogleSuccess = async (idToken: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const success = await login(idToken);
      if (success) {
        router.push('/home');
      } else {
        setError(t('error'));
      }
    } catch {
      setError(t('error'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleError = (errorMessage: string) => {
    setError(errorMessage);
  };

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const result = await loginWithPassword(email, password);
      if (result.success) {
        router.push('/home');
      } else {
        // Map error codes to user-friendly messages
        if (result.error === 'ACCESS_DENIED') {
          setError(t('accessDenied'));
        } else {
          setError(t('invalidCredentials'));
        }
      }
    } catch {
      setError(t('error'));
    } finally {
      setIsLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="relative flex min-h-screen overflow-hidden">
      {/* Decorative blobs */}
      <div className="blob blob-orange blob-animate absolute -top-32 -right-32 h-96 w-96 opacity-60" />
      <div className="blob blob-orange absolute -bottom-24 -left-24 h-80 w-80 opacity-40" />
      <div className="blob blob-green absolute top-1/3 -left-16 h-48 w-48 opacity-30" />
      <div className="blob blob-cream absolute bottom-1/4 right-1/4 h-64 w-64 opacity-50" />

      {/* Main content */}
      <div className="relative z-10 flex flex-1 flex-col items-center justify-center px-4 py-12">
        {/* Logo & Brand */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-3xl bg-primary shadow-soft-lg">
            <GraduationCap className="h-10 w-10 text-white" />
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-foreground">
            AI Mentor
          </h1>
          <p className="mt-1 text-sm font-medium text-muted-foreground">
            {t('tagline')}
          </p>
        </div>

        {/* Login Card */}
        <div className="w-full max-w-sm">
          <div className="card-elevated p-8">
            <div className="mb-6 text-center">
              <h2 className="text-xl font-bold text-foreground">{t('title')}</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                {t('subtitle')}
              </p>
            </div>

            <div className="flex flex-col space-y-4">
              {/* Email/Password Form */}
              <form onSubmit={handlePasswordLogin} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email">{t('email')}</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="student@school.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    disabled={isLoading}
                    autoComplete="email"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password">{t('password')}</Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    disabled={isLoading}
                    autoComplete="current-password"
                  />
                </div>

                <Button
                  type="submit"
                  className="w-full"
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      {t('loading')}
                    </>
                  ) : (
                    t('signIn')
                  )}
                </Button>
              </form>

              {/* Divider */}
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-card px-2 text-muted-foreground">
                    {t('or')}
                  </span>
                </div>
              </div>

              {/* Google Sign-In */}
              <div className="flex flex-col items-center">
                {isLoading ? (
                  <div className="flex items-center space-x-2 text-muted-foreground">
                    <Loader2 className="h-5 w-5 animate-spin" />
                    <span>{t('loading')}</span>
                  </div>
                ) : (
                  <GoogleSignInButton
                    onSuccess={handleGoogleSuccess}
                    onError={handleGoogleError}
                  />
                )}
              </div>

              {/* Error message */}
              {error && (
                <p className="text-center text-sm text-destructive">{error}</p>
              )}
            </div>
          </div>

          {/* Features preview */}
          <div className="mt-8 grid grid-cols-2 gap-4">
            <div className="flex items-center gap-3 rounded-xl bg-white/60 p-3 backdrop-blur-sm">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                <BookOpen className="h-5 w-5 text-primary" />
              </div>
              <span className="text-xs font-medium text-foreground">
                {t('features.adaptive')}
              </span>
            </div>
            <div className="flex items-center gap-3 rounded-xl bg-white/60 p-3 backdrop-blur-sm">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-success/10">
                <Sparkles className="h-5 w-5 text-success" />
              </div>
              <span className="text-xs font-medium text-foreground">
                {t('features.interactive')}
              </span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <p className="mt-12 text-center text-xs text-muted-foreground">
          {t('footer')}
        </p>
      </div>
    </div>
  );
}
