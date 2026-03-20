'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { format } from 'date-fns';
import { Users, Search, Shield, GraduationCap, UserCircle, School } from 'lucide-react';
import { RoleGuard } from '@/components/auth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useGlobalUsers } from '@/lib/hooks/use-global-users';

const ROLES = [
  { value: 'all', label: 'Все роли', labelKz: 'Барлық рөлдер' },
  { value: 'super_admin', label: 'Суперадмин', labelKz: 'Суперәкімші' },
  { value: 'admin', label: 'Администратор', labelKz: 'Әкімші' },
  { value: 'teacher', label: 'Учитель', labelKz: 'Мұғалім' },
  { value: 'student', label: 'Ученик', labelKz: 'Оқушы' },
  { value: 'parent', label: 'Родитель', labelKz: 'Ата-ана' },
] as const;

const ROLE_COLORS: Record<string, string> = {
  super_admin: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  admin: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  teacher: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  student: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  parent: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
};

const ROLE_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  super_admin: Shield,
  admin: Shield,
  teacher: GraduationCap,
  student: Users,
  parent: UserCircle,
};

const AUTH_LABELS: Record<string, string> = {
  local: 'Email',
  google: 'Google',
  apple: 'Apple',
  phone: 'Телефон',
};

const PAGE_SIZE = 20;

export default function UsersPage() {
  const t = useTranslations('roles');
  const tUsers = useTranslations('users');
  const tCommon = useTranslations('common');

  const [page, setPage] = useState(1);
  const [role, setRole] = useState<string>('all');
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const { data, isLoading } = useGlobalUsers({
    page,
    page_size: PAGE_SIZE,
    role: role === 'all' ? undefined : role,
    is_active: statusFilter === 'all' ? undefined : statusFilter === 'active',
    search: search || undefined,
  });

  const users = data?.items || [];
  const total = data?.total || 0;
  const totalPages = data?.total_pages || 1;

  const handleSearch = () => {
    setSearch(searchInput);
    setPage(1);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch();
  };

  const roleCounts = users.reduce(
    (acc, u) => {
      acc[u.role] = (acc[u.role] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <RoleGuard allowedRoles={['super_admin']}>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{tUsers('title')}</h1>
          <p className="text-muted-foreground">{tUsers('description')}</p>
        </div>

        {/* Stats Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          {ROLES.filter((r) => r.value !== 'all').map((r) => {
            const Icon = ROLE_ICONS[r.value] || Users;
            return (
              <Card
                key={r.value}
                className={`cursor-pointer transition-colors ${role === r.value ? 'border-primary' : ''}`}
                onClick={() => {
                  setRole(role === r.value ? 'all' : r.value);
                  setPage(1);
                }}
              >
                <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                  <CardTitle className="text-sm font-medium">{t(r.value)}</CardTitle>
                  <Icon className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {role === r.value ? total : '—'}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder={tUsers('searchPlaceholder')}
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyDown={handleKeyDown}
              className="pl-9"
            />
          </div>
          <Select value={role} onValueChange={(v) => { setRole(v); setPage(1); }}>
            <SelectTrigger className="w-[200px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {ROLES.map((r) => (
                <SelectItem key={r.value} value={r.value}>
                  {r.value === 'all' ? tCommon('all') : t(r.value)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setPage(1); }}>
            <SelectTrigger className="w-[160px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{tCommon('all')}</SelectItem>
              <SelectItem value="active">{tCommon('active')}</SelectItem>
              <SelectItem value="inactive">{tCommon('inactive')}</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={handleSearch} variant="secondary">
            <Search className="h-4 w-4 mr-2" />
            {tCommon('search')}
          </Button>
        </div>

        {/* Table */}
        <div className="rounded-md border overflow-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">#</TableHead>
                <TableHead>{tUsers('fullName')}</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>{tUsers('role')}</TableHead>
                <TableHead>{tUsers('school')}</TableHead>
                <TableHead>{tUsers('authProvider')}</TableHead>
                <TableHead>{tCommon('status')}</TableHead>
                <TableHead>{tUsers('registeredAt')}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                Array.from({ length: 10 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 8 }).map((_, j) => (
                      <TableCell key={j}>
                        <Skeleton className="h-4 w-full" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : users.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="h-24 text-center text-muted-foreground">
                    {tCommon('noResults')}
                  </TableCell>
                </TableRow>
              ) : (
                users.map((user, index) => (
                  <TableRow key={user.id}>
                    <TableCell className="text-muted-foreground">
                      {(page - 1) * PAGE_SIZE + index + 1}
                    </TableCell>
                    <TableCell>
                      <div className="font-medium">
                        {user.last_name} {user.first_name}
                      </div>
                      {user.middle_name && (
                        <div className="text-xs text-muted-foreground">{user.middle_name}</div>
                      )}
                    </TableCell>
                    <TableCell className="text-sm">{user.email}</TableCell>
                    <TableCell>
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${ROLE_COLORS[user.role] || 'bg-gray-100 text-gray-800'}`}
                      >
                        {t(user.role)}
                      </span>
                    </TableCell>
                    <TableCell>
                      {user.school_name ? (
                        <div className="flex items-center gap-1.5">
                          <School className="h-3.5 w-3.5 text-muted-foreground" />
                          <span className="text-sm">{user.school_name}</span>
                        </div>
                      ) : (
                        <span className="text-sm text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">
                        {AUTH_LABELS[user.auth_provider || 'local'] || user.auth_provider}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {user.is_active ? (
                        <Badge variant="default" className="bg-green-600 text-xs">
                          {tCommon('active')}
                        </Badge>
                      ) : (
                        <Badge variant="secondary" className="text-xs">
                          {tCommon('inactive')}
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {format(new Date(user.created_at), 'dd.MM.yyyy')}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              {tUsers('totalUsers')}: <span className="font-medium">{total}</span>
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
              >
                {tCommon('previous')}
              </Button>
              <span className="text-sm text-muted-foreground">
                {page} / {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
              >
                {tCommon('next')}
              </Button>
            </div>
          </div>
        )}
      </div>
    </RoleGuard>
  );
}
