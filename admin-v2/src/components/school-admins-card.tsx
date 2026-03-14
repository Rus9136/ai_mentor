'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { KeyRound, UserCircle } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useSchoolAdmins, useResetAdminPassword } from '@/lib/hooks/use-schools';

interface SchoolAdminsCardProps {
  schoolId: number;
}

export function SchoolAdminsCard({ schoolId }: SchoolAdminsCardProps) {
  const t = useTranslations('schools');
  const { data: admins, isLoading } = useSchoolAdmins(schoolId);
  const resetPassword = useResetAdminPassword();

  const [resetDialogOpen, setResetDialogOpen] = useState(false);
  const [selectedAdminId, setSelectedAdminId] = useState<number | null>(null);
  const [newPassword, setNewPassword] = useState('');

  const handleResetPassword = () => {
    if (!selectedAdminId || newPassword.length < 6) return;
    resetPassword.mutate(
      { schoolId, adminId: selectedAdminId, password: newPassword },
      {
        onSuccess: () => {
          setResetDialogOpen(false);
          setNewPassword('');
          setSelectedAdminId(null);
        },
      }
    );
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-16 w-full" />
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>{t('adminsTitle')}</CardTitle>
          <CardDescription>{t('adminsDescription')}</CardDescription>
        </CardHeader>
        <CardContent>
          {!admins || admins.length === 0 ? (
            <p className="text-sm text-muted-foreground">{t('noAdmins')}</p>
          ) : (
            <div className="space-y-3">
              {admins.map((admin) => (
                <div
                  key={admin.id}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
                  <div className="flex items-center gap-3">
                    <UserCircle className="h-8 w-8 text-muted-foreground" />
                    <div>
                      <p className="font-medium">
                        {admin.last_name} {admin.first_name}
                        {admin.middle_name ? ` ${admin.middle_name}` : ''}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {admin.email}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={admin.is_active ? 'default' : 'secondary'}>
                      {admin.is_active ? 'Активен' : 'Неактивен'}
                    </Badge>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setSelectedAdminId(admin.id);
                        setNewPassword('');
                        setResetDialogOpen(true);
                      }}
                    >
                      <KeyRound className="mr-1 h-3 w-3" />
                      {t('resetPassword')}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={resetDialogOpen} onOpenChange={setResetDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('resetPassword')}</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <Input
              type="password"
              placeholder={t('newPassword')}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              minLength={6}
            />
            {newPassword.length > 0 && newPassword.length < 6 && (
              <p className="mt-1 text-sm text-destructive">Минимум 6 символов</p>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setResetDialogOpen(false)}
            >
              Отмена
            </Button>
            <Button
              onClick={handleResetPassword}
              disabled={newPassword.length < 6 || resetPassword.isPending}
            >
              {resetPassword.isPending ? 'Сохранение...' : t('resetPasswordConfirm')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
