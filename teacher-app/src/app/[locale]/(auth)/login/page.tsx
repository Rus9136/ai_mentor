'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { useAuth } from '@/providers/auth-provider';
import { getErrorMessage } from '@/lib/api/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2, GraduationCap, AlertCircle, Mail, Phone } from 'lucide-react';

type LoginMode = 'email' | 'phone';

/** Format 10 raw digits as +7 (XXX) XXX-XX-XX */
function formatPhoneDisplay(digits: string): string {
  if (!digits) return '+7';
  let r = '+7 (';
  r += digits.slice(0, 3);
  if (digits.length >= 3) r += ') ';
  if (digits.length > 3) r += digits.slice(3, 6);
  if (digits.length > 6) r += '-' + digits.slice(6, 8);
  if (digits.length > 8) r += '-' + digits.slice(8, 10);
  return r;
}

/** Extract up to 10 subscriber digits from any input */
function extractPhoneDigits(input: string): string {
  let digits = input.replace(/\D/g, '');
  // Strip country code prefix if user typed/pasted it
  if (digits.startsWith('87') && digits.length >= 11) digits = digits.slice(1);
  if (digits.startsWith('7') && digits.length >= 11) digits = digits.slice(1);
  return digits.slice(0, 10);
}

export default function LoginPage() {
  const t = useTranslations('auth');
  const { login } = useAuth();

  const [mode, setMode] = useState<LoginMode>('email');
  const [email, setEmail] = useState('');
  const [phoneDigits, setPhoneDigits] = useState(''); // raw 10 digits
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const loginValue = mode === 'email' ? email : (phoneDigits ? `+7${phoneDigits}` : '');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await login(loginValue, password);
    } catch (err) {
      if (err instanceof Error && err.message === 'ACCESS_DENIED') {
        setError(t('accessDenied'));
      } else {
        setError(getErrorMessage(err));
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-background to-muted/30 px-4">
      {/* Logo */}
      <div className="mb-8 flex flex-col items-center">
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary shadow-lg">
          <GraduationCap className="h-8 w-8 text-white" />
        </div>
        <h1 className="text-2xl font-bold text-foreground">AI Mentor</h1>
        <p className="text-sm text-muted-foreground">Teacher Dashboard</p>
      </div>

      {/* Login Card */}
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-xl">{t('login')}</CardTitle>
          <CardDescription>{t('loginDescription')}</CardDescription>
        </CardHeader>
        <CardContent>
          {/* Login mode tabs */}
          <div className="mb-4 flex rounded-lg border p-1">
            <button
              type="button"
              onClick={() => setMode('email')}
              className={`flex flex-1 items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                mode === 'email'
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <Mail className="h-4 w-4" />
              {t('loginByEmail')}
            </button>
            <button
              type="button"
              onClick={() => setMode('phone')}
              className={`flex flex-1 items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                mode === 'phone'
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <Phone className="h-4 w-4" />
              {t('loginByPhone')}
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {mode === 'email' ? (
              <div className="space-y-2">
                <Label htmlFor="email">{t('email')}</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="teacher@school.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  disabled={isLoading}
                  autoComplete="email"
                />
              </div>
            ) : (
              <div className="space-y-2">
                <Label htmlFor="phone">{t('phone')}</Label>
                <Input
                  id="phone"
                  type="tel"
                  placeholder="+7 (707) 123-45-67"
                  value={phoneDigits ? formatPhoneDisplay(phoneDigits) : ''}
                  onChange={(e) => setPhoneDigits(extractPhoneDigits(e.target.value))}
                  required
                  disabled={isLoading}
                  autoComplete="tel"
                />
              </div>
            )}

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

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t('loggingIn')}
                </>
              ) : (
                t('signIn')
              )}
            </Button>
          </form>

          <div className="mt-4 text-center text-sm">
            <span className="text-muted-foreground">{t('noAccount')}</span>{' '}
            <Link href="/register" className="text-primary hover:underline font-medium">
              {t('goToRegister')}
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* Footer */}
      <p className="mt-8 text-center text-xs text-muted-foreground">
        AI Mentor &copy; 2025
      </p>
    </div>
  );
}
