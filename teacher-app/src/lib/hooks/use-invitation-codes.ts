import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { useTranslations } from 'next-intl';
import {
  getClassInvitationCodes,
  createInvitationCode,
  deactivateInvitationCode,
  CreateInvitationCodeData,
} from '@/lib/api/invitation-codes';

/**
 * Hook to get invitation codes for a class
 */
export function useClassInvitationCodes(classId: number, isActive?: boolean) {
  return useQuery({
    queryKey: ['teacher', 'invitation-codes', classId, isActive],
    queryFn: () => getClassInvitationCodes(classId, isActive),
    enabled: !!classId,
  });
}

/**
 * Hook to create a new invitation code
 */
export function useCreateInvitationCode(classId: number) {
  const queryClient = useQueryClient();
  const t = useTranslations('invitationCodes');

  return useMutation({
    mutationFn: (data: CreateInvitationCodeData) => createInvitationCode(classId, data),
    onSuccess: () => {
      toast.success(t('createSuccess'));
      queryClient.invalidateQueries({ queryKey: ['teacher', 'invitation-codes', classId] });
    },
    onError: () => {
      toast.error(t('createError'));
    },
  });
}

/**
 * Hook to deactivate an invitation code
 */
export function useDeactivateInvitationCode(classId: number) {
  const queryClient = useQueryClient();
  const t = useTranslations('invitationCodes');

  return useMutation({
    mutationFn: (codeId: number) => deactivateInvitationCode(classId, codeId),
    onSuccess: () => {
      toast.success(t('deactivateSuccess'));
      queryClient.invalidateQueries({ queryKey: ['teacher', 'invitation-codes', classId] });
    },
    onError: () => {
      toast.error(t('deactivateError'));
    },
  });
}
