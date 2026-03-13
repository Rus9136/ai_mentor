'use client';

import { useState, useRef } from 'react';
import { useTranslations } from 'next-intl';
import { Copy, Trash2, Calendar, Users, Check, Loader2, QrCode, Download } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import { formatRelativeDate } from '@/lib/utils';
import type { InvitationCode } from '@/lib/api/invitation-codes';

interface InvitationCodeCardProps {
  code: InvitationCode;
  onDeactivate: (id: number) => void;
  isDeactivating?: boolean;
}

export function InvitationCodeCard({
  code,
  onDeactivate,
  isDeactivating,
}: InvitationCodeCardProps) {
  const t = useTranslations('invitationCodes');
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showQrDialog, setShowQrDialog] = useState(false);
  const [copied, setCopied] = useState(false);
  const qrRef = useRef<HTMLDivElement>(null);

  const onboardingUrl = `https://ai-mentor.kz/onboarding?code=${code.code}`;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code.code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDeactivate = () => {
    onDeactivate(code.id);
    setShowDeleteDialog(false);
  };

  const handleDownloadQr = () => {
    const svg = qrRef.current?.querySelector('svg');
    if (!svg) return;
    const svgData = new XMLSerializer().serializeToString(svg);
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx?.drawImage(img, 0, 0);
      const a = document.createElement('a');
      a.download = `invite-${code.code}.png`;
      a.href = canvas.toDataURL('image/png');
      a.click();
    };
    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
  };

  const isExpired = code.expires_at && new Date(code.expires_at) < new Date();
  const isExhausted = code.max_uses !== null && code.uses_count >= code.max_uses;
  const isInactive = !code.is_active || isExpired || isExhausted;

  return (
    <>
      <Card className={`hover:shadow-md transition-shadow ${isInactive ? 'opacity-60' : ''}`}>
        <CardContent className="pt-4">
          <div className="flex items-start justify-between gap-4">
            {/* Code info */}
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <code className="px-3 py-1.5 bg-muted rounded-md text-lg font-mono font-bold tracking-wider">
                  {code.code}
                </code>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={handleCopy}
                  className="h-8 w-8 p-0"
                >
                  {copied ? (
                    <Check className="h-4 w-4 text-green-500" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
                {!isInactive && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setShowQrDialog(true)}
                    className="h-8 w-8 p-0"
                    title={t('showQr')}
                  >
                    <QrCode className="h-4 w-4" />
                  </Button>
                )}
                {!code.is_active && (
                  <Badge variant="secondary">{t('inactive')}</Badge>
                )}
                {isExpired && code.is_active && (
                  <Badge variant="destructive">{t('expired')}</Badge>
                )}
                {isExhausted && code.is_active && !isExpired && (
                  <Badge variant="secondary">{t('exhausted')}</Badge>
                )}
              </div>

              {/* Meta info */}
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
                <div className="flex items-center gap-1">
                  <Users className="h-3.5 w-3.5" />
                  <span>
                    {code.uses_count}
                    {code.max_uses !== null ? ` / ${code.max_uses}` : ''} {t('uses')}
                  </span>
                </div>
                {code.expires_at && (
                  <div className="flex items-center gap-1">
                    <Calendar className="h-3.5 w-3.5" />
                    <span>
                      {t('expiresAt')}: {new Date(code.expires_at).toLocaleDateString()}
                    </span>
                  </div>
                )}
                <span>{t('createdAt')}: {formatRelativeDate(code.created_at)}</span>
              </div>
            </div>

            {/* Actions */}
            {code.is_active && (
              <Button
                size="sm"
                variant="ghost"
                className="text-destructive hover:bg-destructive/10"
                onClick={() => setShowDeleteDialog(true)}
                disabled={isDeactivating}
              >
                {isDeactivating ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* QR Code Dialog */}
      <Dialog open={showQrDialog} onOpenChange={setShowQrDialog}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>{t('qrTitle')}</DialogTitle>
            <DialogDescription>
              {t('qrDescription')}
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col items-center gap-4 py-4">
            <div ref={qrRef} className="rounded-lg bg-white p-4">
              <QRCodeSVG
                value={onboardingUrl}
                size={200}
                level="M"
                marginSize={2}
              />
            </div>
            <code className="rounded-md bg-muted px-3 py-1.5 text-sm font-mono font-bold tracking-wider">
              {code.code}
            </code>
          </div>
          <DialogFooter>
            <Button variant="outline" size="sm" onClick={handleDownloadQr}>
              <Download className="mr-2 h-4 w-4" />
              {t('downloadQr')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('deactivateTitle')}</DialogTitle>
            <DialogDescription>
              {t('deactivateDescription', { code: code.code })}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>
              {t('cancel')}
            </Button>
            <Button variant="destructive" onClick={handleDeactivate}>
              {t('confirmDeactivate')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
