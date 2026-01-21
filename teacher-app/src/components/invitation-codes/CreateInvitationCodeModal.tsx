'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Loader2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';

interface CreateInvitationCodeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: {
    expires_at?: string | null;
    max_uses?: number | null;
  }) => void;
  isLoading?: boolean;
  className?: string;
}

export function CreateInvitationCodeModal({
  isOpen,
  onClose,
  onSubmit,
  isLoading,
  className,
}: CreateInvitationCodeModalProps) {
  const t = useTranslations('invitationCodes');

  const [hasExpiry, setHasExpiry] = useState(true);
  const [expiryDays, setExpiryDays] = useState(30);
  const [hasMaxUses, setHasMaxUses] = useState(false);
  const [maxUses, setMaxUses] = useState(50);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const data: { expires_at?: string | null; max_uses?: number | null } = {};

    if (hasExpiry && expiryDays > 0) {
      const expiryDate = new Date();
      expiryDate.setDate(expiryDate.getDate() + expiryDays);
      data.expires_at = expiryDate.toISOString();
    }

    if (hasMaxUses && maxUses > 0) {
      data.max_uses = maxUses;
    }

    onSubmit(data);
  };

  const handleClose = () => {
    // Reset form on close
    setHasExpiry(true);
    setExpiryDays(30);
    setHasMaxUses(false);
    setMaxUses(50);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{t('createTitle')}</DialogTitle>
          <DialogDescription>
            {t('createDescription', { className: className || '' })}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Expiry setting */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="hasExpiry"
                checked={hasExpiry}
                onCheckedChange={(checked) => setHasExpiry(checked === true)}
              />
              <Label htmlFor="hasExpiry" className="font-normal">
                {t('setExpiry')}
              </Label>
            </div>
            {hasExpiry && (
              <div className="ml-6 flex items-center gap-2">
                <Input
                  type="number"
                  min={1}
                  max={365}
                  value={expiryDays}
                  onChange={(e) => setExpiryDays(Number(e.target.value))}
                  className="w-20"
                />
                <span className="text-sm text-muted-foreground">{t('days')}</span>
              </div>
            )}
          </div>

          {/* Max uses setting */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="hasMaxUses"
                checked={hasMaxUses}
                onCheckedChange={(checked) => setHasMaxUses(checked === true)}
              />
              <Label htmlFor="hasMaxUses" className="font-normal">
                {t('setMaxUses')}
              </Label>
            </div>
            {hasMaxUses && (
              <div className="ml-6 flex items-center gap-2">
                <Input
                  type="number"
                  min={1}
                  max={1000}
                  value={maxUses}
                  onChange={(e) => setMaxUses(Number(e.target.value))}
                  className="w-24"
                />
                <span className="text-sm text-muted-foreground">{t('students')}</span>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>
              {t('cancel')}
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {t('create')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
