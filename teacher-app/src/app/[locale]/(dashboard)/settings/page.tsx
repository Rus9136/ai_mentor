'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { useAuth } from '@/providers/auth-provider';
import { changePassword, getErrorMessage } from '@/lib/api/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Loader2, CheckCircle2, AlertCircle, KeyRound } from 'lucide-react';

export default function SettingsPage() {
  const t = useTranslations('settings');
  const { user } = useAuth();

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    if (newPassword !== confirmPassword) {
      setError(t('passwordMismatch'));
      return;
    }

    if (newPassword.length < 8) {
      setError(t('passwordTooShort'));
      return;
    }

    setIsLoading(true);
    try {
      await changePassword(currentPassword, newPassword);
      setSuccess(true);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{t('title')}</h1>
        <p className="text-muted-foreground">{t('description')}</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* User info card */}
        <Card>
          <CardHeader>
            <CardTitle>{t('profile')}</CardTitle>
            <CardDescription>{t('profileDescription')}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1">
              <Label className="text-muted-foreground">{t('fullName')}</Label>
              <p className="text-sm font-medium">
                {user?.last_name} {user?.first_name} {user?.middle_name || ''}
              </p>
            </div>
            {user?.email && !user.email.includes('@phone.local') && (
              <div className="space-y-1">
                <Label className="text-muted-foreground">Email</Label>
                <p className="text-sm font-medium">{user.email}</p>
              </div>
            )}
            {user?.phone && (
              <div className="space-y-1">
                <Label className="text-muted-foreground">{t('phone')}</Label>
                <p className="text-sm font-medium">{user.phone}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Change password card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <KeyRound className="h-5 w-5" />
              {t('changePassword')}
            </CardTitle>
            <CardDescription>{t('changePasswordDescription')}</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {success && (
                <Alert className="border-green-200 bg-green-50 text-green-800">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <AlertDescription className="text-green-800">
                    {t('passwordChanged')}
                  </AlertDescription>
                </Alert>
              )}

              <div className="space-y-2">
                <Label htmlFor="currentPassword">{t('currentPassword')}</Label>
                <Input
                  id="currentPassword"
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                  disabled={isLoading}
                  autoComplete="current-password"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="newPassword">{t('newPassword')}</Label>
                <Input
                  id="newPassword"
                  type="password"
                  placeholder={t('minChars')}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  disabled={isLoading}
                  autoComplete="new-password"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmPassword">{t('confirmPassword')}</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  disabled={isLoading}
                  autoComplete="new-password"
                />
              </div>

              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {t('saving')}
                  </>
                ) : (
                  t('savePassword')
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
