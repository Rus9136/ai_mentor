'use client';

import { use, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { ArrowLeft, Edit, UserPlus, GraduationCap, Users, X, Calendar, Hash } from 'lucide-react';
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
import {
  useClass,
  useStudents,
  useTeachers,
  useAddStudentsToClass,
  useRemoveStudentFromClass,
  useAddTeachersToClass,
  useRemoveTeacherFromClass,
} from '@/lib/hooks';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function ClassDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const classId = parseInt(id);
  const t = useTranslations('classes');
  const router = useRouter();
  const locale = 'ru';

  const { data: schoolClass, isLoading } = useClass(classId);
  const { data: allStudents = [] } = useStudents();
  const { data: allTeachers = [] } = useTeachers();

  const addStudents = useAddStudentsToClass();
  const removeStudent = useRemoveStudentFromClass();
  const addTeachers = useAddTeachersToClass();
  const removeTeacher = useRemoveTeacherFromClass();

  const [addStudentsDialogOpen, setAddStudentsDialogOpen] = useState(false);
  const [addTeachersDialogOpen, setAddTeachersDialogOpen] = useState(false);
  const [selectedStudents, setSelectedStudents] = useState<number[]>([]);
  const [selectedTeachers, setSelectedTeachers] = useState<number[]>([]);

  // Filter available students/teachers
  const availableStudents = allStudents.filter(
    (s) => !schoolClass?.students?.some((cs) => cs.id === s.id)
  );
  const availableTeachers = allTeachers.filter(
    (t) => !schoolClass?.teachers?.some((ct) => ct.id === t.id)
  );

  const handleAddStudents = () => {
    if (selectedStudents.length > 0) {
      addStudents.mutate(
        { classId, studentIds: selectedStudents },
        {
          onSuccess: () => {
            setAddStudentsDialogOpen(false);
            setSelectedStudents([]);
          },
        }
      );
    }
  };

  const handleAddTeachers = () => {
    if (selectedTeachers.length > 0) {
      addTeachers.mutate(
        { classId, teacherIds: selectedTeachers },
        {
          onSuccess: () => {
            setAddTeachersDialogOpen(false);
            setSelectedTeachers([]);
          },
        }
      );
    }
  };

  if (isLoading) {
    return (
      <RoleGuard allowedRoles={['admin']}>
        <div className="space-y-6">
          <div className="flex items-center gap-4">
            <Skeleton className="h-10 w-10" />
            <Skeleton className="h-10 w-64" />
          </div>
          <Skeleton className="h-[400px] w-full" />
        </div>
      </RoleGuard>
    );
  }

  if (!schoolClass) {
    return (
      <RoleGuard allowedRoles={['admin']}>
        <div className="flex flex-col items-center justify-center py-12">
          <p className="text-muted-foreground">Класс не найден</p>
          <Button variant="link" onClick={() => router.back()}>
            Вернуться назад
          </Button>
        </div>
      </RoleGuard>
    );
  }

  return (
    <RoleGuard allowedRoles={['admin']}>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => router.back()}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">{schoolClass.name}</h1>
              <p className="text-muted-foreground">
                {schoolClass.academic_year} учебный год
              </p>
            </div>
          </div>
          <Button onClick={() => router.push(`/${locale}/classes/${classId}/edit`)}>
            <Edit className="mr-2 h-4 w-4" />
            {t('edit')}
          </Button>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <Hash className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Код</p>
                  <code className="font-mono">{schoolClass.code}</code>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <Users className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Учеников</p>
                  <p className="text-2xl font-bold">{schoolClass.students?.length || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <GraduationCap className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Учителей</p>
                  <p className="text-2xl font-bold">{schoolClass.teachers?.length || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="students">
          <TabsList>
            <TabsTrigger value="students">
              <Users className="mr-2 h-4 w-4" />
              Ученики ({schoolClass.students?.length || 0})
            </TabsTrigger>
            <TabsTrigger value="teachers">
              <GraduationCap className="mr-2 h-4 w-4" />
              Учителя ({schoolClass.teachers?.length || 0})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="students" className="mt-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0">
                <div>
                  <CardTitle>{t('studentsCount')}</CardTitle>
                  <CardDescription>Список учеников класса</CardDescription>
                </div>
                <Button
                  size="sm"
                  onClick={() => setAddStudentsDialogOpen(true)}
                  disabled={availableStudents.length === 0}
                >
                  <UserPlus className="mr-2 h-4 w-4" />
                  {t('addStudents')}
                </Button>
              </CardHeader>
              <CardContent>
                {schoolClass.students && schoolClass.students.length > 0 ? (
                  <div className="space-y-2">
                    {schoolClass.students.map((student) => (
                      <div
                        key={student.id}
                        className="flex items-center justify-between rounded-lg border p-3"
                      >
                        <div>
                          <div className="font-medium">
                            {student.user?.last_name} {student.user?.first_name}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {student.user?.email}
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => removeStudent.mutate({ classId, studentId: student.id })}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground py-4 text-center">
                    В классе пока нет учеников
                  </p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="teachers" className="mt-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0">
                <div>
                  <CardTitle>{t('teachersCount')}</CardTitle>
                  <CardDescription>Список учителей класса</CardDescription>
                </div>
                <Button
                  size="sm"
                  onClick={() => setAddTeachersDialogOpen(true)}
                  disabled={availableTeachers.length === 0}
                >
                  <UserPlus className="mr-2 h-4 w-4" />
                  {t('addTeachers')}
                </Button>
              </CardHeader>
              <CardContent>
                {schoolClass.teachers && schoolClass.teachers.length > 0 ? (
                  <div className="space-y-2">
                    {schoolClass.teachers.map((teacher) => (
                      <div
                        key={teacher.id}
                        className="flex items-center justify-between rounded-lg border p-3"
                      >
                        <div>
                          <div className="font-medium">
                            {teacher.user?.last_name} {teacher.user?.first_name}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {teacher.subject || teacher.user?.email}
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => removeTeacher.mutate({ classId, teacherId: teacher.id })}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground py-4 text-center">
                    В классе пока нет учителей
                  </p>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Add Students Dialog */}
        <Dialog open={addStudentsDialogOpen} onOpenChange={setAddStudentsDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Добавить учеников</DialogTitle>
              <DialogDescription>
                Выберите учеников для добавления в класс
              </DialogDescription>
            </DialogHeader>
            <div className="max-h-[300px] space-y-2 overflow-y-auto">
              {availableStudents.map((student) => (
                <div
                  key={student.id}
                  className="flex items-center space-x-2 rounded-lg border p-3"
                >
                  <Checkbox
                    id={`student-${student.id}`}
                    checked={selectedStudents.includes(student.id)}
                    onCheckedChange={(checked) => {
                      setSelectedStudents((prev) =>
                        checked
                          ? [...prev, student.id]
                          : prev.filter((id) => id !== student.id)
                      );
                    }}
                  />
                  <label htmlFor={`student-${student.id}`} className="flex-1 cursor-pointer">
                    <span className="font-medium">
                      {student.user?.last_name} {student.user?.first_name}
                    </span>
                    <span className="ml-2 text-sm text-muted-foreground">
                      {student.grade_level} кл.
                    </span>
                  </label>
                </div>
              ))}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setAddStudentsDialogOpen(false)}>
                Отмена
              </Button>
              <Button
                onClick={handleAddStudents}
                disabled={selectedStudents.length === 0 || addStudents.isPending}
              >
                Добавить ({selectedStudents.length})
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Add Teachers Dialog */}
        <Dialog open={addTeachersDialogOpen} onOpenChange={setAddTeachersDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Добавить учителей</DialogTitle>
              <DialogDescription>
                Выберите учителей для добавления в класс
              </DialogDescription>
            </DialogHeader>
            <div className="max-h-[300px] space-y-2 overflow-y-auto">
              {availableTeachers.map((teacher) => (
                <div
                  key={teacher.id}
                  className="flex items-center space-x-2 rounded-lg border p-3"
                >
                  <Checkbox
                    id={`teacher-${teacher.id}`}
                    checked={selectedTeachers.includes(teacher.id)}
                    onCheckedChange={(checked) => {
                      setSelectedTeachers((prev) =>
                        checked
                          ? [...prev, teacher.id]
                          : prev.filter((id) => id !== teacher.id)
                      );
                    }}
                  />
                  <label htmlFor={`teacher-${teacher.id}`} className="flex-1 cursor-pointer">
                    <span className="font-medium">
                      {teacher.user?.last_name} {teacher.user?.first_name}
                    </span>
                    {teacher.subject && (
                      <span className="ml-2 text-sm text-muted-foreground">
                        {teacher.subject}
                      </span>
                    )}
                  </label>
                </div>
              ))}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setAddTeachersDialogOpen(false)}>
                Отмена
              </Button>
              <Button
                onClick={handleAddTeachers}
                disabled={selectedTeachers.length === 0 || addTeachers.isPending}
              >
                Добавить ({selectedTeachers.length})
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </RoleGuard>
  );
}
