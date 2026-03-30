'use client';

import { use, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { ArrowLeft, Edit, UserPlus, GraduationCap, Users, X, Hash, Star, ChevronDown } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { RoleGuard } from '@/components/auth';
import {
  useClass,
  useStudents,
  useTeachers,
  useAddStudentsToClass,
  useRemoveStudentFromClass,
  useAddTeachersToClass,
  useRemoveTeacherFromClass,
  useSetHomeroom,
} from '@/lib/hooks';
import { useSubjects } from '@/lib/hooks/use-goso';
import type { Teacher, ClassTeacherInfo } from '@/types';

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
  const { data: subjects = [] } = useSubjects();

  const addStudents = useAddStudentsToClass();
  const removeStudent = useRemoveStudentFromClass();
  const addTeachers = useAddTeachersToClass();
  const removeTeacher = useRemoveTeacherFromClass();
  const setHomeroom = useSetHomeroom();

  const [addStudentsDialogOpen, setAddStudentsDialogOpen] = useState(false);
  const [addTeacherDialogOpen, setAddTeacherDialogOpen] = useState(false);
  const [selectedStudents, setSelectedStudents] = useState<number[]>([]);

  // Add teacher form state
  const [selectedTeacherId, setSelectedTeacherId] = useState<string>('');
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>('');
  const [isHomeroomChecked, setIsHomeroomChecked] = useState(false);

  // Use teacher_assignments for display (falls back to teachers for backward compat)
  const teacherAssignments: ClassTeacherInfo[] = schoolClass?.teacher_assignments || [];

  // Get available teachers (not yet assigned, or assigned but for different subjects)
  const assignedTeacherIds = new Set(teacherAssignments.map((a) => a.teacher_id));

  // Get subjects for selected teacher
  const selectedTeacher = allTeachers.find((t) => t.id === Number(selectedTeacherId));
  const teacherSubjects = selectedTeacher?.subjects || [];

  // Filter already assigned (teacher_id, subject_id) pairs
  const assignedPairs = new Set(
    teacherAssignments.map((a) => `${a.teacher_id}-${a.subject_id ?? 'null'}`)
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

  const handleAddTeacher = () => {
    if (!selectedTeacherId || !selectedSubjectId) return;

    const teacherId = Number(selectedTeacherId);
    const subjectId = Number(selectedSubjectId);

    // Check if this exact pair is already assigned
    if (assignedPairs.has(`${teacherId}-${subjectId}`)) return;

    addTeachers.mutate(
      {
        classId,
        assignments: [{
          teacher_id: teacherId,
          subject_id: subjectId,
          is_homeroom: isHomeroomChecked,
        }],
      },
      {
        onSuccess: () => {
          setAddTeacherDialogOpen(false);
          setSelectedTeacherId('');
          setSelectedSubjectId('');
          setIsHomeroomChecked(false);
        },
      }
    );
  };

  const handleRemoveTeacher = (assignment: ClassTeacherInfo) => {
    removeTeacher.mutate({
      classId,
      teacherId: assignment.teacher_id,
      subjectId: assignment.subject_id,
    });
  };

  const handleSetHomeroom = (assignment: ClassTeacherInfo) => {
    if (assignment.is_homeroom) return; // Already homeroom
    setHomeroom.mutate({ classId, teacherId: assignment.teacher_id });
  };

  // Filter available students
  const availableStudents = allStudents.filter(
    (s) => !schoolClass?.students?.some((cs) => cs.id === s.id)
  );

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
                  <p className="text-2xl font-bold">{teacherAssignments.length}</p>
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
              Учителя ({teacherAssignments.length})
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
                  <CardDescription>Учителя класса по предметам</CardDescription>
                </div>
                <Button
                  size="sm"
                  onClick={() => setAddTeacherDialogOpen(true)}
                >
                  <UserPlus className="mr-2 h-4 w-4" />
                  Добавить учителя
                </Button>
              </CardHeader>
              <CardContent>
                {teacherAssignments.length > 0 ? (
                  <div className="space-y-2">
                    {teacherAssignments.map((assignment) => (
                      <div
                        key={assignment.id}
                        className="flex items-center justify-between rounded-lg border p-3"
                      >
                        <div className="flex items-center gap-3">
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-medium">
                                {assignment.last_name} {assignment.first_name}
                              </span>
                              {assignment.is_homeroom && (
                                <Badge variant="secondary" className="text-xs">
                                  <Star className="mr-1 h-3 w-3" />
                                  КР
                                </Badge>
                              )}
                            </div>
                            <div className="text-sm text-muted-foreground">
                              {assignment.subject_name || 'Предмет не указан'}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-1">
                          {!assignment.is_homeroom && (
                            <Button
                              variant="ghost"
                              size="sm"
                              title="Назначить классным руководителем"
                              onClick={() => handleSetHomeroom(assignment)}
                              disabled={setHomeroom.isPending}
                            >
                              <Star className="h-4 w-4" />
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleRemoveTeacher(assignment)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
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

        {/* Add Teacher Dialog */}
        <Dialog open={addTeacherDialogOpen} onOpenChange={(open) => {
          setAddTeacherDialogOpen(open);
          if (!open) {
            setSelectedTeacherId('');
            setSelectedSubjectId('');
            setIsHomeroomChecked(false);
          }
        }}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Добавить учителя</DialogTitle>
              <DialogDescription>
                Выберите учителя и предмет для назначения в класс
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              {/* Teacher select */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Учитель</label>
                <Select
                  value={selectedTeacherId}
                  onValueChange={(val) => {
                    setSelectedTeacherId(val);
                    setSelectedSubjectId('');
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Выберите учителя" />
                  </SelectTrigger>
                  <SelectContent>
                    {allTeachers.map((teacher) => (
                      <SelectItem key={teacher.id} value={String(teacher.id)}>
                        {teacher.user?.last_name} {teacher.user?.first_name}
                        {teacher.subjects && teacher.subjects.length > 0 && (
                          <span className="text-muted-foreground ml-2">
                            ({teacher.subjects.map((s) => s.name_ru).join(', ')})
                          </span>
                        )}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Subject select (from teacher's subjects) */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Предмет</label>
                <Select
                  value={selectedSubjectId}
                  onValueChange={setSelectedSubjectId}
                  disabled={!selectedTeacherId}
                >
                  <SelectTrigger>
                    <SelectValue placeholder={selectedTeacherId ? 'Выберите предмет' : 'Сначала выберите учителя'} />
                  </SelectTrigger>
                  <SelectContent>
                    {teacherSubjects.length > 0 ? (
                      teacherSubjects.map((subject) => {
                        const isAssigned = assignedPairs.has(`${selectedTeacherId}-${subject.id}`);
                        return (
                          <SelectItem
                            key={subject.id}
                            value={String(subject.id)}
                            disabled={isAssigned}
                          >
                            {subject.name_ru}
                            {isAssigned && ' (уже назначен)'}
                          </SelectItem>
                        );
                      })
                    ) : selectedTeacherId ? (
                      // Fallback: show all subjects if teacher has no subjects assigned
                      subjects.map((subject) => (
                        <SelectItem key={subject.id} value={String(subject.id)}>
                          {subject.name_ru}
                        </SelectItem>
                      ))
                    ) : null}
                  </SelectContent>
                </Select>
              </div>

              {/* Homeroom checkbox */}
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="is-homeroom"
                  checked={isHomeroomChecked}
                  onCheckedChange={(checked) => setIsHomeroomChecked(checked === true)}
                />
                <label htmlFor="is-homeroom" className="text-sm cursor-pointer">
                  Классный руководитель
                </label>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setAddTeacherDialogOpen(false)}>
                Отмена
              </Button>
              <Button
                onClick={handleAddTeacher}
                disabled={!selectedTeacherId || !selectedSubjectId || addTeachers.isPending}
              >
                Добавить
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </RoleGuard>
  );
}
