'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useClassDetail } from '@/lib/hooks/use-teacher-data';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { MasteryDistributionChart } from '@/components/dashboard/MasteryDistributionChart';
import { MasteryBadge } from '@/components/dashboard/MasteryBadge';
import { Button } from '@/components/ui/button';
import { Link } from '@/i18n/routing';
import {
  ArrowLeft,
  Users,
  Loader2,
  ChevronRight,
  UserPlus,
  Plus,
  Key,
} from 'lucide-react';
import { formatRelativeDate } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { usePendingCounts } from '@/lib/hooks/use-join-requests';
import {
  useClassInvitationCodes,
  useCreateInvitationCode,
  useDeactivateInvitationCode,
} from '@/lib/hooks/use-invitation-codes';
import { InvitationCodeCard, CreateInvitationCodeModal } from '@/components/invitation-codes';

export default function ClassDetailPage() {
  const params = useParams();
  const classId = Number(params.id);
  const t = useTranslations('classes');
  const tInvite = useTranslations('invitationCodes');

  const [showCreateCodeModal, setShowCreateCodeModal] = useState(false);

  const { data: classData, isLoading, error } = useClassDetail(classId);
  const { data: pendingCounts } = usePendingCounts();
  const { data: invitationCodes, isLoading: isLoadingCodes } = useClassInvitationCodes(classId);
  const createCodeMutation = useCreateInvitationCode(classId);
  const deactivateCodeMutation = useDeactivateInvitationCode(classId);

  const pendingForClass = pendingCounts?.find(c => c.class_id === classId)?.pending_count || 0;
  const activeCodesCount = invitationCodes?.filter(c => c.is_active).length || 0;

  if (isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !classData) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center">
        <p className="text-muted-foreground">Class not found</p>
        <Link href="/classes">
          <Button variant="link" className="mt-2">
            <ArrowLeft className="mr-2 h-4 w-4" />
            {t('title')}
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/classes">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-foreground">{classData.name}</h1>
            <p className="text-muted-foreground">
              {classData.grade_level} класс • {classData.academic_year}
            </p>
          </div>
        </div>
        <Link href={`/classes/${classId}/requests`}>
          <Button variant="outline" size="sm" className="gap-2">
            <UserPlus className="h-4 w-4" />
            {t('joinRequests')}
            {pendingForClass > 0 && (
              <Badge variant="destructive">{pendingForClass}</Badge>
            )}
          </Button>
        </Link>
      </div>

      {/* Stats row */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-primary/10 p-2">
                <Users className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold">{classData.students_count}</p>
                <p className="text-sm text-muted-foreground">{t('students')}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="text-2xl font-bold">{classData.progress_percentage}%</p>
            <p className="text-sm text-muted-foreground">{t('averageProgress')}</p>
            <Progress value={classData.progress_percentage} className="mt-2 h-2" />
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardContent className="pt-6">
            <p className="mb-2 text-sm font-medium text-muted-foreground">
              Распределение по уровням
            </p>
            <MasteryDistributionChart distribution={classData.mastery_distribution} />
          </CardContent>
        </Card>
      </div>

      {/* Invitation Codes Section */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <div className="flex items-center gap-2">
            <Key className="h-5 w-5 text-muted-foreground" />
            <CardTitle className="text-lg">{tInvite('title')}</CardTitle>
            {activeCodesCount > 0 && (
              <Badge variant="secondary">{activeCodesCount}</Badge>
            )}
          </div>
          <Button size="sm" onClick={() => setShowCreateCodeModal(true)}>
            <Plus className="h-4 w-4 mr-1" />
            {tInvite('createButton')}
          </Button>
        </CardHeader>
        <CardContent>
          {isLoadingCodes ? (
            <div className="flex justify-center py-4">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : invitationCodes && invitationCodes.length > 0 ? (
            <div className="space-y-3">
              {invitationCodes.map((code) => (
                <InvitationCodeCard
                  key={code.id}
                  code={code}
                  onDeactivate={(id) => deactivateCodeMutation.mutate(id)}
                  isDeactivating={deactivateCodeMutation.isPending}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-6 text-muted-foreground">
              <Key className="h-10 w-10 mx-auto mb-2 opacity-50" />
              <p>{tInvite('noCodesYet')}</p>
              <p className="text-sm">{tInvite('noCodesDescription')}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Invitation Code Modal */}
      <CreateInvitationCodeModal
        isOpen={showCreateCodeModal}
        onClose={() => setShowCreateCodeModal(false)}
        onSubmit={(data) => {
          createCodeMutation.mutate(data, {
            onSuccess: () => setShowCreateCodeModal(false),
          });
        }}
        isLoading={createCodeMutation.isPending}
        className={classData.name}
      />

      {/* Students table */}
      <Card>
        <CardHeader>
          <CardTitle>{t('studentsList')}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Ученик</th>
                  <th>{t('masteryLevel')}</th>
                  <th>{t('progress')}</th>
                  <th>{t('lastActivity')}</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {classData.students.map((student) => (
                  <tr key={student.id}>
                    <td>
                      <div className="flex items-center gap-3">
                        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-sm font-medium text-primary">
                          {student.first_name[0]}
                          {student.last_name[0]}
                        </div>
                        <div>
                          <p className="font-medium text-foreground">
                            {student.last_name} {student.first_name}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {student.student_code}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td>
                      <MasteryBadge level={student.mastery_level} showLabel />
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        <Progress
                          value={student.progress_percentage}
                          className="h-2 w-20"
                        />
                        <span className="text-sm text-muted-foreground">
                          {student.progress_percentage}%
                        </span>
                      </div>
                    </td>
                    <td>
                      <span className="text-sm text-muted-foreground">
                        {student.last_activity
                          ? formatRelativeDate(student.last_activity)
                          : t('neverActive')}
                      </span>
                    </td>
                    <td>
                      <Link
                        href={`/classes/${classId}/students/${student.id}`}
                        className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
                      >
                        Подробнее
                        <ChevronRight className="h-4 w-4" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
