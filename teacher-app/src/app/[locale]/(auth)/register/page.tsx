'use client';

import { useState, useEffect } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { Link } from '@/i18n/routing';
import { useAuth } from '@/providers/auth-provider';
import {
  getRegistrationSubjects,
  getRegistrationClasses,
  getErrorMessage,
  SubjectOption,
  ClassOption,
} from '@/lib/api/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PhoneInput } from '@/components/ui/phone-input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Loader2,
  GraduationCap,
  AlertCircle,
  Mail,
  Phone,
} from 'lucide-react';

type LoginMode = 'email' | 'phone';

export default function RegisterPage() {
  const t = useTranslations('auth');
  const locale = useLocale();
  const { registerAndLogin } = useAuth();

  const [mode, setMode] = useState<LoginMode>('email');
  const [schoolCode, setSchoolCode] = useState('');
  const [email, setEmail] = useState('');
  const [phoneDigits, setPhoneDigits] = useState('');
  const [lastName, setLastName] = useState('');
  const [firstName, setFirstName] = useState('');
  const [middleName, setMiddleName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [selectedSubjects, setSelectedSubjects] = useState<Set<number>>(
    new Set()
  );
  const [subjects, setSubjects] = useState<SubjectOption[]>([]);
  const [subjectsLoading, setSubjectsLoading] = useState(true);
  const [selectedClasses, setSelectedClasses] = useState<Set<number>>(
    new Set()
  );
  const [classes, setClasses] = useState<ClassOption[]>([]);
  const [classesLoading, setClassesLoading] = useState(false);
  const [schoolCodeValidated, setSchoolCodeValidated] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    getRegistrationSubjects()
      .then(setSubjects)
      .catch(() => {})
      .finally(() => setSubjectsLoading(false));
  }, []);

  const loadClasses = async (code: string) => {
    if (!code.trim()) {
      setClasses([]);
      setSelectedClasses(new Set());
      setSchoolCodeValidated(false);
      return;
    }
    setClassesLoading(true);
    try {
      const result = await getRegistrationClasses(code.trim());
      setClasses(result);
      setSchoolCodeValidated(true);
    } catch {
      setClasses([]);
      setSchoolCodeValidated(false);
    } finally {
      setClassesLoading(false);
    }
  };

  const toggleSubject = (id: number) => {
    setSelectedSubjects((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const toggleClass = (id: number) => {
    setSelectedClasses((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError(t('passwordsDoNotMatch'));
      return;
    }
    if (selectedSubjects.size === 0) {
      setError(t('selectSubjectsError'));
      return;
    }

    setIsLoading(true);
    try {
      await registerAndLogin({
        school_code: schoolCode,
        first_name: firstName,
        last_name: lastName,
        middle_name: middleName || undefined,
        email: mode === 'email' ? email : undefined,
        phone: mode === 'phone' ? `+7${phoneDigits}` : undefined,
        password,
        subject_ids: Array.from(selectedSubjects),
        class_ids: selectedClasses.size > 0 ? Array.from(selectedClasses) : undefined,
      });
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-background to-muted/30 px-4 py-8">
      {/* Logo */}
      <div className="mb-6 flex flex-col items-center">
        <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary shadow-lg">
          <GraduationCap className="h-7 w-7 text-white" />
        </div>
        <h1 className="text-2xl font-bold text-foreground">AI Mentor</h1>
        <p className="text-sm text-muted-foreground">Teacher Dashboard</p>
      </div>

      {/* Register Card */}
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-xl">{t('register')}</CardTitle>
          <CardDescription>{t('registerDescription')}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* School Code */}
            <div className="space-y-2">
              <Label htmlFor="schoolCode">{t('schoolCode')}</Label>
              <Input
                id="schoolCode"
                type="text"
                placeholder={t('schoolCodePlaceholder')}
                value={schoolCode}
                onChange={(e) => {
                  setSchoolCode(e.target.value);
                  setSchoolCodeValidated(false);
                }}
                onBlur={() => loadClasses(schoolCode)}
                required
                disabled={isLoading}
              />
            </div>

            {/* Login mode tabs */}
            <div className="flex rounded-lg border p-1">
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
                {t('registerByEmail')}
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
                {t('registerByPhone')}
              </button>
            </div>

            {/* Email or Phone */}
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
                <PhoneInput
                  id="phone"
                  digits={phoneDigits}
                  onDigitsChange={setPhoneDigits}
                  required
                  disabled={isLoading}
                  autoComplete="tel"
                />
              </div>
            )}

            {/* Personal Info */}
            <div className="space-y-2">
              <Label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                {t('personalInfo')}
              </Label>
              <Input
                placeholder={t('lastName')}
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                required
                disabled={isLoading}
                autoComplete="family-name"
              />
              <Input
                placeholder={t('firstName')}
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                required
                disabled={isLoading}
                autoComplete="given-name"
              />
              <Input
                placeholder={t('middleName')}
                value={middleName}
                onChange={(e) => setMiddleName(e.target.value)}
                disabled={isLoading}
                autoComplete="additional-name"
              />
            </div>

            {/* Password */}
            <div className="space-y-2">
              <Label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                {t('loginData')}
              </Label>
              <Input
                type="password"
                placeholder={t('password')}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                disabled={isLoading}
                autoComplete="new-password"
              />
              <Input
                type="password"
                placeholder={t('confirmPassword')}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                minLength={8}
                disabled={isLoading}
                autoComplete="new-password"
              />
            </div>

            {/* Subjects */}
            <div className="space-y-2">
              <Label>{t('subjects')}</Label>
              <p className="text-xs text-muted-foreground">
                {t('subjectsHint')}
              </p>
              {subjectsLoading ? (
                <div className="flex items-center justify-center py-4">
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                </div>
              ) : (
                <div className="max-h-48 space-y-1 overflow-y-auto rounded-md border p-3">
                  {subjects.map((subject) => (
                    <label
                      key={subject.id}
                      className="flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 hover:bg-muted/50"
                    >
                      <Checkbox
                        checked={selectedSubjects.has(subject.id)}
                        onCheckedChange={() => toggleSubject(subject.id)}
                        disabled={isLoading}
                      />
                      <span className="text-sm">
                        {locale === 'kz' ? subject.name_kz : subject.name_ru}
                      </span>
                    </label>
                  ))}
                </div>
              )}
            </div>

            {/* Classes (loaded after school code) */}
            <div className="space-y-2">
              <Label>{t('classes')}</Label>
              <p className="text-xs text-muted-foreground">
                {t('classesHint')}
              </p>
              {!schoolCodeValidated ? (
                <p className="text-xs text-muted-foreground italic py-2">
                  {t('classesLoading')}
                </p>
              ) : classesLoading ? (
                <div className="flex items-center justify-center py-4">
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                </div>
              ) : classes.length === 0 ? (
                <p className="text-xs text-muted-foreground italic py-2">
                  {t('noClasses')}
                </p>
              ) : (
                <div className="max-h-48 space-y-1 overflow-y-auto rounded-md border p-3">
                  {classes.map((cls) => (
                    <label
                      key={cls.id}
                      className="flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 hover:bg-muted/50"
                    >
                      <Checkbox
                        checked={selectedClasses.has(cls.id)}
                        onCheckedChange={() => toggleClass(cls.id)}
                        disabled={isLoading}
                      />
                      <span className="text-sm">
                        {cls.name}
                        <span className="ml-1 text-muted-foreground">
                          ({cls.grade_level} класс)
                        </span>
                      </span>
                    </label>
                  ))}
                </div>
              )}
            </div>

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t('registering')}
                </>
              ) : (
                t('registerButton')
              )}
            </Button>
          </form>

          <div className="mt-4 text-center text-sm">
            <span className="text-muted-foreground">
              {t('alreadyHaveAccount')}
            </span>{' '}
            <Link
              href="/login"
              className="font-medium text-primary hover:underline"
            >
              {t('goToLogin')}
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* Footer */}
      <p className="mt-6 text-center text-xs text-muted-foreground">
        AI Mentor &copy; 2025
      </p>
    </div>
  );
}
