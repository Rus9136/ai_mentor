'use client';

import { useState } from 'react';
import { format } from 'date-fns';
import {
  CreditCard,
  Building2,
  BarChart3,
  Plus,
  Pencil,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { RoleGuard } from '@/components/auth';
import {
  useSubscriptionPlans,
  useSchoolSubscriptions,
  useUsageOverview,
  useCreatePlan,
  useUpdatePlan,
  useAssignPlan,
} from '@/lib/hooks/use-subscriptions';
import type {
  SubscriptionPlan,
  SubscriptionPlanCreate,
  SchoolSubscriptionCreate,
} from '@/lib/api/subscriptions';
import { useQuery } from '@tanstack/react-query';
import { schoolsApi } from '@/lib/api/schools';
import { toast } from 'sonner';

const FEATURE_LABELS: Record<string, string> = {
  chat: 'Чат ученика',
  rag: 'RAG / Объяснения',
  teacher_chat: 'Чат учителя',
  lesson_plan: 'Планы уроков',
};

function formatLimit(val: number | null | undefined): string {
  if (val === null || val === undefined) return '\u221E';
  return val.toString();
}

// ── Plans Tab ──

function PlansTab() {
  const { data: plans, isLoading } = useSubscriptionPlans(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingPlan, setEditingPlan] = useState<SubscriptionPlan | null>(null);
  const createPlan = useCreatePlan();
  const updatePlan = useUpdatePlan();

  const [form, setForm] = useState<SubscriptionPlanCreate>({
    name: '',
    display_name: '',
    daily_message_limit: null,
    feature_limits: {},
    description: '',
    sort_order: 0,
    price_monthly_kzt: null,
    price_yearly_kzt: null,
  });

  const openCreate = () => {
    setEditingPlan(null);
    setForm({
      name: '',
      display_name: '',
      daily_message_limit: null,
      feature_limits: { chat: 20, rag: 10, teacher_chat: 30, lesson_plan: 3 },
      description: '',
      sort_order: 0,
      price_monthly_kzt: null,
      price_yearly_kzt: null,
    });
    setDialogOpen(true);
  };

  const openEdit = (plan: SubscriptionPlan) => {
    setEditingPlan(plan);
    setForm({
      name: plan.name,
      display_name: plan.display_name,
      daily_message_limit: plan.daily_message_limit,
      feature_limits: plan.feature_limits || {},
      description: plan.description || '',
      sort_order: plan.sort_order,
      price_monthly_kzt: plan.price_monthly_kzt,
      price_yearly_kzt: plan.price_yearly_kzt,
    });
    setDialogOpen(true);
  };

  const handleSave = async () => {
    try {
      if (editingPlan) {
        await updatePlan.mutateAsync({
          id: editingPlan.id,
          data: {
            display_name: form.display_name,
            daily_message_limit: form.daily_message_limit,
            feature_limits: form.feature_limits,
            description: form.description || undefined,
            sort_order: form.sort_order,
            price_monthly_kzt: form.price_monthly_kzt,
            price_yearly_kzt: form.price_yearly_kzt,
          },
        });
        toast.success('Тариф обновлен');
      } else {
        await createPlan.mutateAsync(form);
        toast.success('Тариф создан');
      }
      setDialogOpen(false);
    } catch {
      toast.error('Ошибка при сохранении тарифа');
    }
  };

  const updateFeatureLimit = (feature: string, value: string) => {
    setForm((prev) => ({
      ...prev,
      feature_limits: {
        ...prev.feature_limits,
        [feature]: value === '' ? undefined! : parseInt(value),
      },
    }));
  };

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-24 w-full" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={openCreate} size="sm">
          <Plus className="h-4 w-4 mr-1" />
          Новый тариф
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {plans?.map((plan) => (
          <Card key={plan.id} className={!plan.is_active ? 'opacity-50' : ''}>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{plan.display_name}</CardTitle>
                <Button variant="ghost" size="icon" onClick={() => openEdit(plan)}>
                  <Pencil className="h-4 w-4" />
                </Button>
              </div>
              <p className="text-sm text-muted-foreground">{plan.description}</p>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Дневной лимит</span>
                  <span className="font-medium">
                    {plan.daily_message_limit !== null
                      ? `${plan.daily_message_limit} сообщ./день`
                      : 'Безлимит'}
                  </span>
                </div>
                {Object.entries(FEATURE_LABELS).map(([key, label]) => (
                  <div key={key} className="flex justify-between text-sm">
                    <span className="text-muted-foreground">{label}</span>
                    <span>{formatLimit(plan.feature_limits?.[key])}</span>
                  </div>
                ))}
                {plan.price_monthly_kzt && (
                  <div className="flex justify-between text-sm pt-2 border-t">
                    <span className="text-muted-foreground">Цена/мес</span>
                    <span className="font-medium">
                      {plan.price_monthly_kzt.toLocaleString()} KZT
                    </span>
                  </div>
                )}
                <div className="pt-2">
                  <Badge variant={plan.is_active ? 'default' : 'secondary'}>
                    {plan.is_active ? 'Активный' : 'Неактивный'}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {editingPlan ? 'Редактировать тариф' : 'Новый тариф'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Код</Label>
                <Input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="basic"
                  disabled={!!editingPlan}
                />
              </div>
              <div>
                <Label>Название</Label>
                <Input
                  value={form.display_name}
                  onChange={(e) => setForm({ ...form, display_name: e.target.value })}
                  placeholder="Базовый"
                />
              </div>
            </div>
            <div>
              <Label>Общий дневной лимит (пусто = безлимит)</Label>
              <Input
                type="number"
                value={form.daily_message_limit ?? ''}
                onChange={(e) =>
                  setForm({
                    ...form,
                    daily_message_limit: e.target.value ? parseInt(e.target.value) : null,
                  })
                }
                placeholder="Безлимит"
              />
            </div>
            <div className="space-y-2">
              <Label>Лимиты по фичам</Label>
              {Object.entries(FEATURE_LABELS).map(([key, label]) => (
                <div key={key} className="flex items-center gap-2">
                  <span className="text-sm w-40">{label}</span>
                  <Input
                    type="number"
                    className="w-24"
                    value={form.feature_limits?.[key] ?? ''}
                    onChange={(e) => updateFeatureLimit(key, e.target.value)}
                    placeholder="\u221E"
                  />
                </div>
              ))}
            </div>
            <div>
              <Label>Описание</Label>
              <Input
                value={form.description || ''}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Цена/мес (KZT)</Label>
                <Input
                  type="number"
                  value={form.price_monthly_kzt ?? ''}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      price_monthly_kzt: e.target.value ? parseInt(e.target.value) : null,
                    })
                  }
                />
              </div>
              <div>
                <Label>Цена/год (KZT)</Label>
                <Input
                  type="number"
                  value={form.price_yearly_kzt ?? ''}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      price_yearly_kzt: e.target.value ? parseInt(e.target.value) : null,
                    })
                  }
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Отмена
            </Button>
            <Button
              onClick={handleSave}
              disabled={createPlan.isPending || updatePlan.isPending}
            >
              {editingPlan ? 'Сохранить' : 'Создать'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ── School Subscriptions Tab ──

function SchoolSubsTab() {
  const { data: subs, isLoading } = useSchoolSubscriptions();
  const { data: plans } = useSubscriptionPlans();
  const { data: schools } = useQuery({
    queryKey: ['schools', 'list'],
    queryFn: () => schoolsApi.getList(),
  });
  const assignPlan = useAssignPlan();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState<SchoolSubscriptionCreate>({
    school_id: 0,
    plan_id: 0,
    notes: '',
  });

  const schoolName = (id: number | null) =>
    schools?.find((s) => s.id === id)?.name || `School #${id}`;

  const handleAssign = async () => {
    try {
      await assignPlan.mutateAsync(form);
      toast.success('Тариф назначен');
      setDialogOpen(false);
    } catch {
      toast.error('Ошибка при назначении тарифа');
    }
  };

  if (isLoading) {
    return <Skeleton className="h-48 w-full" />;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button
          onClick={() => {
            setForm({ school_id: 0, plan_id: 0, notes: '' });
            setDialogOpen(true);
          }}
          size="sm"
        >
          <Plus className="h-4 w-4 mr-1" />
          Назначить тариф
        </Button>
      </div>

      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Школа</TableHead>
              <TableHead>Тариф</TableHead>
              <TableHead>Статус</TableHead>
              <TableHead>Начало</TableHead>
              <TableHead>Истекает</TableHead>
              <TableHead>Переопределения</TableHead>
              <TableHead>Примечание</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {subs?.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                  Нет назначенных подписок. Все школы используют тариф &ldquo;Бесплатный&rdquo; по
                  умолчанию.
                </TableCell>
              </TableRow>
            )}
            {subs?.map((sub) => (
              <TableRow key={sub.id}>
                <TableCell className="font-medium">
                  {sub.plan?.display_name ? schoolName(sub.school_id) : schoolName(sub.school_id)}
                </TableCell>
                <TableCell>
                  <Badge variant="outline">{sub.plan?.display_name || `Plan #${sub.plan_id}`}</Badge>
                </TableCell>
                <TableCell>
                  <Badge variant={sub.is_active ? 'default' : 'secondary'}>
                    {sub.is_active ? 'Активна' : 'Неактивна'}
                  </Badge>
                </TableCell>
                <TableCell className="text-sm">
                  {format(new Date(sub.starts_at), 'dd.MM.yyyy')}
                </TableCell>
                <TableCell className="text-sm">
                  {sub.expires_at
                    ? format(new Date(sub.expires_at), 'dd.MM.yyyy')
                    : 'Бессрочно'}
                </TableCell>
                <TableCell className="text-sm">
                  {sub.limit_overrides
                    ? Object.entries(sub.limit_overrides)
                        .map(([k, v]) => `${k}: ${v}`)
                        .join(', ')
                    : '-'}
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {sub.notes || '-'}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      {/* Assign Plan Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Назначить тариф школе</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Школа</Label>
              <Select
                value={form.school_id ? form.school_id.toString() : ''}
                onValueChange={(v) => setForm({ ...form, school_id: parseInt(v) })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Выберите школу" />
                </SelectTrigger>
                <SelectContent>
                  {schools?.map((school) => (
                    <SelectItem key={school.id} value={school.id.toString()}>
                      {school.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Тариф</Label>
              <Select
                value={form.plan_id ? form.plan_id.toString() : ''}
                onValueChange={(v) => setForm({ ...form, plan_id: parseInt(v) })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Выберите тариф" />
                </SelectTrigger>
                <SelectContent>
                  {plans?.map((plan) => (
                    <SelectItem key={plan.id} value={plan.id.toString()}>
                      {plan.display_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Примечание</Label>
              <Input
                value={form.notes || ''}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                placeholder="Необязательно"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Отмена
            </Button>
            <Button
              onClick={handleAssign}
              disabled={!form.school_id || !form.plan_id || assignPlan.isPending}
            >
              Назначить
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ── Usage Tab ──

function UsageTab() {
  const { data, isLoading } = useUsageOverview();
  const { data: schools } = useQuery({
    queryKey: ['schools', 'list'],
    queryFn: () => schoolsApi.getList(),
  });

  const schoolName = (id: number | null) =>
    schools?.find((s) => s.id === id)?.name || `School #${id}`;

  if (isLoading) {
    return <Skeleton className="h-48 w-full" />;
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Использование сообщений за сегодня ({data?.date})
      </p>

      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Школа</TableHead>
              <TableHead className="text-right">Сообщений</TableHead>
              <TableHead className="text-right">Токенов</TableHead>
              <TableHead className="text-right">Активных пользователей</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(!data?.schools || data.schools.length === 0) && (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                  Нет данных за сегодня
                </TableCell>
              </TableRow>
            )}
            {data?.schools?.map((s, i) => (
              <TableRow key={i}>
                <TableCell className="font-medium">{schoolName(s.school_id)}</TableCell>
                <TableCell className="text-right">{s.total_messages}</TableCell>
                <TableCell className="text-right">
                  {s.total_tokens.toLocaleString()}
                </TableCell>
                <TableCell className="text-right">{s.active_users}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}

// ── Main Page ──

export default function SubscriptionsPage() {
  return (
    <RoleGuard allowedRoles={['super_admin']}>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Подписки и лимиты</h1>
          <p className="text-muted-foreground">
            Управление тарифами, подписками школ и мониторинг использования
          </p>
        </div>

        <Tabs defaultValue="plans">
          <TabsList>
            <TabsTrigger value="plans" className="gap-1">
              <CreditCard className="h-4 w-4" />
              Тарифы
            </TabsTrigger>
            <TabsTrigger value="schools" className="gap-1">
              <Building2 className="h-4 w-4" />
              Школы
            </TabsTrigger>
            <TabsTrigger value="usage" className="gap-1">
              <BarChart3 className="h-4 w-4" />
              Использование
            </TabsTrigger>
          </TabsList>

          <TabsContent value="plans" className="mt-4">
            <PlansTab />
          </TabsContent>

          <TabsContent value="schools" className="mt-4">
            <SchoolSubsTab />
          </TabsContent>

          <TabsContent value="usage" className="mt-4">
            <UsageTab />
          </TabsContent>
        </Tabs>
      </div>
    </RoleGuard>
  );
}
