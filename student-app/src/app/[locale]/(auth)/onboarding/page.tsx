'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { useAuth } from '@/providers/auth-provider';
import { useRouter } from '@/i18n/routing';
import { validateCode, completeOnboarding } from '@/lib/api/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Loader2, CheckCircle, AlertCircle, UserCircle } from 'lucide-react';

type OnboardingStep = 'code' | 'profile';

interface CodeValidation {
  schoolName: string;
  className: string | null;
  gradeLevel: number;
}

export default function OnboardingPage() {
  const t = useTranslations('auth.onboarding');
  const commonT = useTranslations('common');
  const { user, refreshUser, setRequiresOnboarding } = useAuth();
  const router = useRouter();

  const [step, setStep] = useState<OnboardingStep>('code');
  const [code, setCode] = useState('');
  const [codeValidation, setCodeValidation] = useState<CodeValidation | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Profile form state
  const [firstName, setFirstName] = useState(user?.first_name || '');
  const [lastName, setLastName] = useState(user?.last_name || '');
  const [middleName, setMiddleName] = useState('');
  const [birthDate, setBirthDate] = useState('');

  const handleSkipOnboarding = () => {
    // Save to localStorage that user skipped onboarding
    if (typeof window !== 'undefined') {
      localStorage.setItem('ai_mentor_skipped_onboarding', 'true');
    }
    setRequiresOnboarding(false);
    router.push('/');
  };

  const handleValidateCode = async () => {
    if (!code.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await validateCode(code.trim().toUpperCase());

      if (response.valid) {
        setCodeValidation({
          schoolName: response.school_name || '',
          className: response.class_name || null,
          gradeLevel: response.grade_level || 0,
        });
        setStep('profile');
      } else {
        setError(response.message || t('codeInvalid'));
      }
    } catch {
      setError(t('codeInvalid'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleCompleteOnboarding = async () => {
    if (!firstName.trim() || !lastName.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      await completeOnboarding({
        code: code.trim().toUpperCase(),
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        middle_name: middleName.trim() || undefined,
        birth_date: birthDate || undefined,
      });

      await refreshUser();
      router.push('/');
    } catch {
      setError('Failed to complete registration');
    } finally {
      setIsLoading(false);
    }
  };

  if (step === 'code') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="space-y-1 text-center">
            <CardTitle className="text-2xl font-bold">
              {t('codeTitle')}
            </CardTitle>
            <CardDescription>{t('codeSubtitle')}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Input
                type="text"
                placeholder={t('codePlaceholder')}
                value={code}
                onChange={(e) => setCode(e.target.value.toUpperCase())}
                className="text-center text-lg font-mono tracking-widest"
                maxLength={12}
                disabled={isLoading}
              />
            </div>

            {error && (
              <div className="flex items-center gap-2 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                <AlertCircle className="h-4 w-4" />
                {error}
              </div>
            )}

            <Button
              className="w-full"
              onClick={handleValidateCode}
              disabled={!code.trim() || isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {commonT('loading')}
                </>
              ) : (
                commonT('continue')
              )}
            </Button>

            <div className="relative my-4">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-white px-2 text-muted-foreground">или</span>
              </div>
            </div>

            <Button
              variant="outline"
              className="w-full"
              onClick={handleSkipOnboarding}
              disabled={isLoading}
            >
              <UserCircle className="mr-2 h-4 w-4" />
              {t('skipCode')}
            </Button>
            <p className="text-center text-xs text-muted-foreground">
              {t('skipCodeHint')}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-2xl font-bold">
            {t('profileTitle')}
          </CardTitle>
          {codeValidation && (
            <div className="mt-4 rounded-md bg-green-50 p-3 text-left">
              <div className="flex items-center gap-2 text-green-700">
                <CheckCircle className="h-5 w-5" />
                <span className="font-medium">{t('schoolInfo')}</span>
              </div>
              <div className="mt-2 text-sm text-green-600">
                <p className="font-medium">{codeValidation.schoolName}</p>
                {codeValidation.className && (
                  <p>
                    {codeValidation.gradeLevel} класс, {codeValidation.className}
                  </p>
                )}
              </div>
            </div>
          )}
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">{t('lastName')}</label>
            <Input
              type="text"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              disabled={isLoading}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">{t('firstName')}</label>
            <Input
              type="text"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              disabled={isLoading}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">{t('middleName')}</label>
            <Input
              type="text"
              value={middleName}
              onChange={(e) => setMiddleName(e.target.value)}
              disabled={isLoading}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">{t('birthDate')}</label>
            <Input
              type="date"
              value={birthDate}
              onChange={(e) => setBirthDate(e.target.value)}
              disabled={isLoading}
            />
          </div>

          {error && (
            <div className="flex items-center gap-2 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              <AlertCircle className="h-4 w-4" />
              {error}
            </div>
          )}

          <div className="flex gap-2">
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => {
                setStep('code');
                setCodeValidation(null);
              }}
              disabled={isLoading}
            >
              {commonT('back')}
            </Button>
            <Button
              className="flex-1"
              onClick={handleCompleteOnboarding}
              disabled={!firstName.trim() || !lastName.trim() || isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {commonT('loading')}
                </>
              ) : (
                t('completeButton')
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
