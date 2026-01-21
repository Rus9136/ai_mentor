'use client';

import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { ArrowLeft, Users, Loader2, UserPlus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Link } from '@/i18n/routing';
import { JoinRequestCard } from '@/components/join-requests/JoinRequestCard';
import {
  useClassPendingRequests,
  useApproveRequest,
  useRejectRequest,
} from '@/lib/hooks/use-join-requests';
import { useClassDetail } from '@/lib/hooks/use-teacher-data';

export default function ClassJoinRequestsPage() {
  const params = useParams();
  const classId = Number(params.id);
  const t = useTranslations('joinRequests');
  const tClasses = useTranslations('classes');

  const { data: classData, isLoading: classLoading } = useClassDetail(classId);
  const { data: requestsData, isLoading: requestsLoading } = useClassPendingRequests(classId);
  const approveRequest = useApproveRequest();
  const rejectRequest = useRejectRequest();

  const isLoading = classLoading || requestsLoading;

  if (isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!classData) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center">
        <p className="text-muted-foreground">{tClasses('notFound')}</p>
        <Link href="/classes">
          <Button variant="link" className="mt-2">
            <ArrowLeft className="mr-2 h-4 w-4" />
            {tClasses('title')}
          </Button>
        </Link>
      </div>
    );
  }

  const requests = requestsData?.items || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href={`/classes/${classId}`}>
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-5 w-5" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-foreground">{t('title')}</h1>
          <p className="text-muted-foreground">
            {classData.name} • {classData.grade_level} {tClasses('grade')}
          </p>
        </div>
      </div>

      {/* Requests list */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <UserPlus className="h-5 w-5" />
              {t('pendingRequests')}
            </CardTitle>
            {requestsData && (
              <span className="text-sm text-muted-foreground">
                {t('totalCount', { count: requestsData.total })}
              </span>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {requests.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Users className="h-12 w-12 text-muted-foreground/50 mb-4" />
              <p className="text-muted-foreground">{t('noRequests')}</p>
            </div>
          ) : (
            <div className="space-y-4">
              {requests.map((request) => (
                <JoinRequestCard
                  key={request.id}
                  request={request}
                  onApprove={(id) => approveRequest.mutate(id)}
                  onReject={(id, reason) => rejectRequest.mutate({ requestId: id, reason })}
                  isApproving={approveRequest.isPending}
                  isRejecting={rejectRequest.isPending}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
