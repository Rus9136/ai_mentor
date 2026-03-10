import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  subscriptionsApi,
  SubscriptionPlanCreate,
  SubscriptionPlanUpdate,
  SchoolSubscriptionCreate,
  SchoolSubscriptionUpdate,
} from '@/lib/api/subscriptions';

export const subscriptionKeys = {
  all: ['subscriptions'] as const,
  plans: () => [...subscriptionKeys.all, 'plans'] as const,
  schoolSubs: () => [...subscriptionKeys.all, 'school-subs'] as const,
  usage: (date?: string) => [...subscriptionKeys.all, 'usage', date] as const,
};

export function useSubscriptionPlans(activeOnly = true) {
  return useQuery({
    queryKey: subscriptionKeys.plans(),
    queryFn: () => subscriptionsApi.listPlans(activeOnly),
  });
}

export function useSchoolSubscriptions() {
  return useQuery({
    queryKey: subscriptionKeys.schoolSubs(),
    queryFn: () => subscriptionsApi.listSchoolSubscriptions(),
  });
}

export function useUsageOverview(date?: string) {
  return useQuery({
    queryKey: subscriptionKeys.usage(date),
    queryFn: () => subscriptionsApi.getUsageOverview(date),
  });
}

export function useCreatePlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: SubscriptionPlanCreate) => subscriptionsApi.createPlan(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: subscriptionKeys.plans() }),
  });
}

export function useUpdatePlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: SubscriptionPlanUpdate }) =>
      subscriptionsApi.updatePlan(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: subscriptionKeys.plans() }),
  });
}

export function useAssignPlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: SchoolSubscriptionCreate) => subscriptionsApi.assignPlan(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: subscriptionKeys.schoolSubs() }),
  });
}

export function useUpdateSubscription() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: SchoolSubscriptionUpdate }) =>
      subscriptionsApi.updateSubscription(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: subscriptionKeys.schoolSubs() }),
  });
}
