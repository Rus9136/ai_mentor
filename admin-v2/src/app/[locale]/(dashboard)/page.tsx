'use client';

import { useTranslations } from 'next-intl';
import { useAuth } from '@/providers/auth-provider';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { School, CheckCircle, Ban, Users } from 'lucide-react';

export default function DashboardPage() {
  const t = useTranslations('dashboard');
  const { user, isSuperAdmin, isSchoolAdmin } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{t('title')}</h1>
        <p className="text-muted-foreground">
          {t('welcome')}, {user?.first_name}!
        </p>
      </div>

      {isSuperAdmin && <SuperAdminDashboard />}
      {isSchoolAdmin && <SchoolAdminDashboard />}
    </div>
  );
}

function SuperAdminDashboard() {
  const t = useTranslations('dashboard');

  // Placeholder metrics - will be replaced with real data
  const metrics = [
    {
      title: t('totalSchools'),
      value: '—',
      icon: School,
      color: 'text-blue-500',
    },
    {
      title: t('activeSchools'),
      value: '—',
      icon: CheckCircle,
      color: 'text-green-500',
    },
    {
      title: t('blockedSchools'),
      value: '—',
      icon: Ban,
      color: 'text-red-500',
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-3">
      {metrics.map((metric) => {
        const Icon = metric.icon;
        return (
          <Card key={metric.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {metric.title}
              </CardTitle>
              <Icon className={`h-5 w-5 ${metric.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{metric.value}</div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

function SchoolAdminDashboard() {
  // Placeholder for school admin dashboard
  const metrics = [
    {
      title: 'Ученики',
      value: '—',
      icon: Users,
      color: 'text-blue-500',
    },
    {
      title: 'Учителя',
      value: '—',
      icon: Users,
      color: 'text-green-500',
    },
    {
      title: 'Классы',
      value: '—',
      icon: School,
      color: 'text-purple-500',
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-3">
      {metrics.map((metric) => {
        const Icon = metric.icon;
        return (
          <Card key={metric.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {metric.title}
              </CardTitle>
              <Icon className={`h-5 w-5 ${metric.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{metric.value}</div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
