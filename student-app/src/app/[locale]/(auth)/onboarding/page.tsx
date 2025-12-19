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
import { Loader2, CheckCircle, AlertCircle, School, ChevronLeft } from 'lucide-react';

// Step types for the new flow
type OnboardingStep = 'grade-select' | 'school-code' | 'profile';

// Grade options with their corresponding public codes
const GRADE_OPTIONS = [
  { grade: 7, code: 'PUBLIC7' },
  { grade: 8, code: 'PUBLIC8' },
  { grade: 9, code: 'PUBLIC9' },
  { grade: 10, code: 'PUBLIC10' },
  { grade: 11, code: 'PUBLIC11' },
];

interface CodeValidation {
  schoolName: string;
  className: string | null;
  gradeLevel: number;
  isPublic: boolean;
}

export default function OnboardingPage() {
  const t = useTranslations('auth.onboarding');
  const commonT = useTranslations('common');
  const { user, refreshUser } = useAuth();
  const router = useRouter();

  // Step management
  const [step, setStep] = useState<OnboardingStep>('grade-select');

  // Grade selection state
  const [selectedGrade, setSelectedGrade] = useState<number | null>(null);

  // Manual code state
  const [manualCode, setManualCode] = useState('');

  // The actual code to use (either from grade selection or manual entry)
  const [activeCode, setActiveCode] = useState('');

  // Validation result
  const [codeValidation, setCodeValidation] = useState<CodeValidation | null>(null);

  // Loading and error states
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Profile form state
  const [firstName, setFirstName] = useState(user?.first_name || '');
  const [lastName, setLastName] = useState(user?.last_name || '');
  const [middleName, setMiddleName] = useState('');
  const [birthDate, setBirthDate] = useState('');

  // Handle grade selection and auto-validate public code
  const handleGradeSelect = async (grade: number) => {
    setSelectedGrade(grade);
    setError(null);
    setIsLoading(true);

    const gradeOption = GRADE_OPTIONS.find((g) => g.grade === grade);
    if (!gradeOption) return;

    try {
      const response = await validateCode(gradeOption.code);

      if (response.valid) {
        setActiveCode(gradeOption.code);
        setCodeValidation({
          schoolName: response.school?.name || t('publicSchoolName'),
          className: response.school_class?.name || null,
          gradeLevel: response.grade_level || grade,
          isPublic: true,
        });
        setStep('profile');
      } else {
        setError(response.error || t('codeInvalid'));
      }
    } catch {
      setError(t('codeInvalid'));
    } finally {
      setIsLoading(false);
    }
  };

  // Handle manual code validation
  const handleValidateManualCode = async () => {
    if (!manualCode.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await validateCode(manualCode.trim().toUpperCase());

      if (response.valid) {
        setActiveCode(manualCode.trim().toUpperCase());
        setCodeValidation({
          schoolName: response.school?.name || '',
          className: response.school_class?.name || null,
          gradeLevel: response.grade_level || 0,
          isPublic: false,
        });
        setStep('profile');
      } else {
        setError(response.error || t('codeInvalid'));
      }
    } catch {
      setError(t('codeInvalid'));
    } finally {
      setIsLoading(false);
    }
  };

  // Handle onboarding completion
  const handleCompleteOnboarding = async () => {
    if (!firstName.trim() || !lastName.trim() || !activeCode) return;

    setIsLoading(true);
    setError(null);

    try {
      await completeOnboarding({
        invitation_code: activeCode,
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

  // Go back to grade selection
  const handleBackToGradeSelection = () => {
    setStep('grade-select');
    setCodeValidation(null);
    setActiveCode('');
    setManualCode('');
    setSelectedGrade(null);
    setError(null);
  };

  // ========================================
  // Step 1: Grade Selection (Default)
  // ========================================
  if (step === 'grade-select') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="space-y-1 text-center">
            <CardTitle className="text-2xl font-bold">
              {t('selectGrade')}
            </CardTitle>
            <CardDescription>{t('selectGradeSubtitle')}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Grade Selection Buttons */}
            <div className="grid grid-cols-1 gap-2">
              {GRADE_OPTIONS.map(({ grade }) => (
                <Button
                  key={grade}
                  variant="outline"
                  className={`h-12 justify-start px-4 text-base ${
                    selectedGrade === grade ? 'border-primary bg-primary/5' : ''
                  }`}
                  onClick={() => handleGradeSelect(grade)}
                  disabled={isLoading}
                >
                  {isLoading && selectedGrade === grade ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : null}
                  {t(`grade${grade}`)}
                </Button>
              ))}
            </div>

            {error && (
              <div className="flex items-center gap-2 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                <AlertCircle className="h-4 w-4" />
                {error}
              </div>
            )}

            {/* Divider */}
            <div className="relative my-4">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-white px-2 text-muted-foreground">
                  {commonT('or')}
                </span>
              </div>
            </div>

            {/* Switch to manual code entry */}
            <Button
              variant="ghost"
              className="w-full"
              onClick={() => setStep('school-code')}
              disabled={isLoading}
            >
              <School className="mr-2 h-4 w-4" />
              {t('haveSchoolCode')}
            </Button>
            <p className="text-center text-xs text-muted-foreground">
              {t('haveSchoolCodeHint')}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // ========================================
  // Step 2: Manual School Code Entry
  // ========================================
  if (step === 'school-code') {
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
                value={manualCode}
                onChange={(e) => setManualCode(e.target.value.toUpperCase())}
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
              onClick={handleValidateManualCode}
              disabled={!manualCode.trim() || isLoading}
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

            {/* Back button */}
            <Button
              variant="ghost"
              className="w-full"
              onClick={handleBackToGradeSelection}
              disabled={isLoading}
            >
              <ChevronLeft className="mr-2 h-4 w-4" />
              {t('backToGradeSelection')}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // ========================================
  // Step 3: Profile Completion
  // ========================================
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
                <span className="font-medium">
                  {codeValidation.isPublic ? t('publicSchoolInfo') : t('schoolInfo')}
                </span>
              </div>
              <div className="mt-2 text-sm text-green-600">
                <p className="font-medium">{codeValidation.schoolName}</p>
                <p>
                  {codeValidation.gradeLevel} класс
                  {codeValidation.className && `, ${codeValidation.className}`}
                </p>
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
              onClick={handleBackToGradeSelection}
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
