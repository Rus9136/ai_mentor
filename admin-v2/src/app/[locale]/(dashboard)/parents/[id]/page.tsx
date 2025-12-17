'use client';

import { use, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Mail, Phone, UserPlus, X } from 'lucide-react';
import { format } from 'date-fns';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Checkbox } from '@/components/ui/checkbox';
import { RoleGuard } from '@/components/auth';
import { useParent, useStudents, useAddChildren, useRemoveChild } from '@/lib/hooks';
import type { Student } from '@/types';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function ParentDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const parentId = parseInt(id);
  const router = useRouter();

  const { data: parent, isLoading } = useParent(parentId);
  const { data: allStudents = [] } = useStudents();
  const addChildren = useAddChildren();
  const removeChild = useRemoveChild();

  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [selectedStudents, setSelectedStudents] = useState<number[]>([]);

  // Filter students not already linked
  const availableStudents = allStudents.filter(
    (s) => !parent?.children?.some((c) => c.id === s.id)
  );

  const handleAddChildren = () => {
    if (selectedStudents.length > 0) {
      addChildren.mutate(
        { parentId, studentIds: selectedStudents },
        {
          onSuccess: () => {
            setAddDialogOpen(false);
            setSelectedStudents([]);
          },
        }
      );
    }
  };

  const handleRemoveChild = (studentId: number) => {
    removeChild.mutate({ parentId, studentId });
  };

  const toggleStudent = (studentId: number) => {
    setSelectedStudents((prev) =>
      prev.includes(studentId)
        ? prev.filter((id) => id !== studentId)
        : [...prev, studentId]
    );
  };

  if (isLoading) {
    return (
      <RoleGuard allowedRoles={['admin']}>
        <div className="space-y-6">
          <div className="flex items-center gap-4">
            <Skeleton className="h-10 w-10" />
            <Skeleton className="h-10 w-64" />
          </div>
          <Card>
            <CardHeader>
              <Skeleton className="h-6 w-48" />
            </CardHeader>
            <CardContent className="space-y-4">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
            </CardContent>
          </Card>
        </div>
      </RoleGuard>
    );
  }

  if (!parent) {
    return (
      <RoleGuard allowedRoles={['admin']}>
        <div className="flex flex-col items-center justify-center py-12">
          <p className="text-muted-foreground">Родитель не найден</p>
          <Button variant="link" onClick={() => router.back()}>
            Вернуться назад
          </Button>
        </div>
      </RoleGuard>
    );
  }

  const user = parent.user;
  const fullName = user
    ? `${user.last_name || ''} ${user.first_name || ''} ${user.middle_name || ''}`.trim()
    : 'Нет данных';

  return (
    <RoleGuard allowedRoles={['admin']}>
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{fullName}</h1>
            <p className="text-muted-foreground">Родитель</p>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Контактные данные</CardTitle>
              <CardDescription>Информация о родителе</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3">
                <Mail className="h-4 w-4 text-muted-foreground" />
                <span>{user?.email || '—'}</span>
              </div>
              {user?.phone && (
                <div className="flex items-center gap-3">
                  <Phone className="h-4 w-4 text-muted-foreground" />
                  <span>{user.phone}</span>
                </div>
              )}

              <Separator />

              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Статус:</span>
                <Badge variant={user?.is_active ? 'default' : 'secondary'}>
                  {user?.is_active ? 'Активен' : 'Неактивен'}
                </Badge>
              </div>

              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Добавлен:</span>
                <span>
                  {format(new Date(parent.created_at), 'dd.MM.yyyy HH:mm')}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <div>
                <CardTitle>Дети</CardTitle>
                <CardDescription>Связанные ученики</CardDescription>
              </div>
              <Button
                size="sm"
                onClick={() => setAddDialogOpen(true)}
                disabled={availableStudents.length === 0}
              >
                <UserPlus className="mr-2 h-4 w-4" />
                Добавить
              </Button>
            </CardHeader>
            <CardContent>
              {parent.children && parent.children.length > 0 ? (
                <div className="space-y-2">
                  {parent.children.map((child: Student) => (
                    <div
                      key={child.id}
                      className="flex items-center justify-between rounded-lg border p-3"
                    >
                      <div>
                        <div className="font-medium">
                          {child.user?.last_name} {child.user?.first_name}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {child.grade_level} класс
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleRemoveChild(child.id)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">
                  Нет связанных учеников
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Добавить детей</DialogTitle>
              <DialogDescription>
                Выберите учеников для привязки к родителю
              </DialogDescription>
            </DialogHeader>
            <div className="max-h-[300px] space-y-2 overflow-y-auto">
              {availableStudents.map((student) => (
                <div
                  key={student.id}
                  className="flex items-center space-x-2 rounded-lg border p-3"
                >
                  <Checkbox
                    id={`add-student-${student.id}`}
                    checked={selectedStudents.includes(student.id)}
                    onCheckedChange={() => toggleStudent(student.id)}
                  />
                  <label
                    htmlFor={`add-student-${student.id}`}
                    className="flex-1 cursor-pointer text-sm"
                  >
                    <span className="font-medium">
                      {student.user?.last_name} {student.user?.first_name}
                    </span>
                    <span className="ml-2 text-muted-foreground">
                      {student.grade_level} класс
                    </span>
                  </label>
                </div>
              ))}
              {availableStudents.length === 0 && (
                <p className="text-center text-sm text-muted-foreground py-4">
                  Все ученики уже привязаны
                </p>
              )}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setAddDialogOpen(false)}>
                Отмена
              </Button>
              <Button
                onClick={handleAddChildren}
                disabled={selectedStudents.length === 0 || addChildren.isPending}
              >
                Добавить ({selectedStudents.length})
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </RoleGuard>
  );
}
