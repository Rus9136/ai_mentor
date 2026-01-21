'use client';

import { useTranslations } from 'next-intl';
import { Clock, XCircle, RefreshCw } from 'lucide-react';
import { JoinRequestStatus as JoinRequestStatusType } from '@/lib/api/join-request';

interface JoinRequestStatusProps {
  status: JoinRequestStatusType;
  onTryAgain?: () => void;
}

export function JoinRequestStatus({ status, onTryAgain }: JoinRequestStatusProps) {
  const t = useTranslations('profile.joinClass');

  if (!status.has_request) {
    return null;
  }

  // Pending status
  if (status.status === 'pending') {
    return (
      <div className="card-flat p-4 border-l-4 border-yellow-400 bg-yellow-50">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-yellow-100 flex-shrink-0">
            <Clock className="h-5 w-5 text-yellow-600" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-medium text-yellow-800">{t('pendingStatus')}</p>
            <p className="text-sm text-yellow-700 mt-0.5">
              {t('pendingDescription', { className: status.class_name || '' })}
            </p>
            {status.school_name && (
              <p className="text-xs text-yellow-600 mt-1">{status.school_name}</p>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Rejected status
  if (status.status === 'rejected') {
    return (
      <div className="card-flat p-4 border-l-4 border-red-400 bg-red-50">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-100 flex-shrink-0">
            <XCircle className="h-5 w-5 text-red-600" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-medium text-red-800">{t('rejectedStatus')}</p>
            {status.rejection_reason && (
              <p className="text-sm text-red-700 mt-0.5">{status.rejection_reason}</p>
            )}
            {status.class_name && (
              <p className="text-xs text-red-600 mt-1">{status.class_name}</p>
            )}
          </div>
        </div>
        {onTryAgain && (
          <button
            onClick={onTryAgain}
            className="mt-3 w-full flex items-center justify-center gap-2 py-2 px-4 rounded-full bg-red-100 text-red-700 font-medium text-sm hover:bg-red-200 transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
            {t('tryAgain')}
          </button>
        )}
      </div>
    );
  }

  return null;
}
