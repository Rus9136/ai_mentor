'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { X, Loader2 } from 'lucide-react';
import { useCreateJoinRequest } from '@/lib/hooks/use-join-request';

interface JoinClassModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export function JoinClassModal({ isOpen, onClose, onSuccess }: JoinClassModalProps) {
  const t = useTranslations('profile.joinClass');
  const [invitationCode, setInvitationCode] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [middleName, setMiddleName] = useState('');
  const [error, setError] = useState<string | null>(null);

  const createRequest = useCreateJoinRequest();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!invitationCode.trim() || !firstName.trim() || !lastName.trim()) {
      return;
    }

    try {
      await createRequest.mutateAsync({
        invitation_code: invitationCode.trim(),
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        middle_name: middleName.trim() || undefined,
      });

      // Reset form and close on success
      setInvitationCode('');
      setFirstName('');
      setLastName('');
      setMiddleName('');
      onSuccess?.();
      onClose();
    } catch (err: unknown) {
      // Extract error message from API response
      const message =
        err instanceof Error
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
            err.message
          : t('errors.unknown');
      setError(message);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-md mx-4 bg-background rounded-2xl shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <h2 className="text-lg font-semibold text-foreground">{t('title')}</h2>
          <button
            onClick={onClose}
            className="p-2 rounded-full hover:bg-muted transition-colors"
          >
            <X className="h-5 w-5 text-muted-foreground" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {/* Error message */}
          {error && (
            <div className="p-3 rounded-lg bg-red-100 text-red-700 text-sm">
              {error}
            </div>
          )}

          {/* Invitation code */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">
              {t('invitationCode')}
            </label>
            <input
              type="text"
              value={invitationCode}
              onChange={(e) => setInvitationCode(e.target.value.toUpperCase())}
              placeholder="7A-XXXXX"
              className="w-full px-4 py-3 rounded-xl border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
              required
            />
          </div>

          {/* Divider with text */}
          <div className="relative py-2">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border" />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="px-2 bg-background text-muted-foreground">
                {t('enterYourData')}
              </span>
            </div>
          </div>

          {/* Last name */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">
              {t('lastName')} *
            </label>
            <input
              type="text"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
              required
            />
          </div>

          {/* First name */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">
              {t('firstName')} *
            </label>
            <input
              type="text"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
              required
            />
          </div>

          {/* Middle name */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">
              {t('middleName')}
            </label>
            <input
              type="text"
              value={middleName}
              onChange={(e) => setMiddleName(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>

          {/* Submit button */}
          <button
            type="submit"
            disabled={
              createRequest.isPending ||
              !invitationCode.trim() ||
              !firstName.trim() ||
              !lastName.trim()
            }
            className="w-full py-3 rounded-full bg-primary text-white font-medium transition-colors hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {createRequest.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                {t('submitting')}
              </>
            ) : (
              t('submit')
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
