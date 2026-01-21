'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Calendar, Check, X, Loader2 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { formatRelativeDate } from '@/lib/utils';
import type { JoinRequestDetail } from '@/lib/api/join-requests';

interface JoinRequestCardProps {
  request: JoinRequestDetail;
  onApprove: (id: number) => void;
  onReject: (id: number, reason?: string) => void;
  isApproving?: boolean;
  isRejecting?: boolean;
}

export function JoinRequestCard({
  request,
  onApprove,
  onReject,
  isApproving,
  isRejecting,
}: JoinRequestCardProps) {
  const t = useTranslations('joinRequests');
  const [showRejectDialog, setShowRejectDialog] = useState(false);
  const [rejectReason, setRejectReason] = useState('');

  const handleReject = () => {
    onReject(request.id, rejectReason || undefined);
    setShowRejectDialog(false);
    setRejectReason('');
  };

  const fullName = [
    request.student_last_name,
    request.student_first_name,
    request.student_middle_name,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <>
      <Card className="hover:shadow-md transition-shadow">
        <CardContent className="pt-4">
          <div className="flex items-start justify-between gap-4">
            {/* Student info */}
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-sm font-medium text-primary">
                {request.student_first_name[0]}
                {request.student_last_name[0]}
              </div>
              <div>
                <p className="font-medium text-foreground">{fullName}</p>
                <p className="text-sm text-muted-foreground">
                  {request.student_code} • {request.student_grade_level} {t('grade')}
                </p>
                {request.student_email && (
                  <p className="text-xs text-muted-foreground">{request.student_email}</p>
                )}
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="outline"
                className="text-destructive border-destructive hover:bg-destructive/10"
                onClick={() => setShowRejectDialog(true)}
                disabled={isApproving || isRejecting}
              >
                {isRejecting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <X className="h-4 w-4" />
                )}
              </Button>
              <Button
                size="sm"
                onClick={() => onApprove(request.id)}
                disabled={isApproving || isRejecting}
              >
                {isApproving ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <Check className="h-4 w-4 mr-2" />
                )}
                {t('approve')}
              </Button>
            </div>
          </div>

          {/* Meta info */}
          <div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              <span>{formatRelativeDate(request.created_at)}</span>
            </div>
            {request.invitation_code && (
              <Badge variant="outline" className="text-xs">
                {request.invitation_code}
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Reject Dialog */}
      <Dialog open={showRejectDialog} onOpenChange={setShowRejectDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('rejectTitle')}</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <p className="text-sm text-muted-foreground mb-4">
              {t('rejectDescription', { name: fullName })}
            </p>
            <Textarea
              placeholder={t('rejectReasonPlaceholder')}
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              rows={3}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRejectDialog(false)}>
              {t('cancel')}
            </Button>
            <Button variant="destructive" onClick={handleReject}>
              {t('confirmReject')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
