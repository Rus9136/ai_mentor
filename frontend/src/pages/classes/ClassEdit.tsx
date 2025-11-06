import React, { useState, useEffect } from 'react';
import {
  Edit,
  SimpleForm,
  TextInput,
  SelectInput,
  useRecordContext,
  useNotify,
  useRefresh,
  required,
  minLength,
  maxLength,
  regex,
} from 'react-admin';
import {
  Typography,
  Divider,
  Box,
  Card,
  CardHeader,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Checkbox,
  Button,
  CircularProgress,
  Grid,
} from '@mui/material';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import type { SchoolClass, Student, Teacher } from '../../types';
import { apiRequest } from '../../providers/dataProvider';

/**
 * Валидация name
 */
const validateName = [
  required('Название класса обязательно для заполнения'),
  minLength(2, 'Название должно содержать минимум 2 символа'),
  maxLength(100, 'Название должно содержать максимум 100 символов'),
];

/**
 * Валидация grade_level
 */
const validateGradeLevel = [required('Класс обязателен для выбора')];

/**
 * Валидация academic_year
 */
const validateAcademicYear = [
  required('Учебный год обязателен для заполнения'),
  regex(
    /^\d{4}\/\d{4}$/,
    'Учебный год должен быть в формате YYYY/YYYY (например, 2024/2025)'
  ),
];

/**
 * Список классов для выбора
 */
const gradeLevelChoices = [
  { id: 7, name: '7 класс' },
  { id: 8, name: '8 класс' },
  { id: 9, name: '9 класс' },
  { id: 10, name: '10 класс' },
  { id: 11, name: '11 класс' },
];

/**
 * Утилита: пересечение двух массивов
 */
function not<T extends { id: number }>(a: T[], b: T[]): T[] {
  return a.filter((value) => !b.find((item) => item.id === value.id));
}

/**
 * Утилита: пересечение двух массивов
 */
function intersection<T extends { id: number }>(a: T[], b: T[]): T[] {
  return a.filter((value) => b.find((item) => item.id === value.id));
}

/**
 * Компонент Transfer List для управления студентами класса
 */
const StudentsTransferList: React.FC<{ classId: number; gradeLevel: number }> = ({
  classId,
  gradeLevel,
}) => {
  const notify = useNotify();
  const refresh = useRefresh();
  const [loading, setLoading] = useState(true);
  const [allStudents, setAllStudents] = useState<Student[]>([]);
  const [assignedStudents, setAssignedStudents] = useState<Student[]>([]);
  const [checkedLeft, setCheckedLeft] = useState<Student[]>([]);
  const [checkedRight, setCheckedRight] = useState<Student[]>([]);

  // Загрузка данных
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Загружаем всех студентов школы (фильтр по grade_level)
        const studentsResponse = await apiRequest('/admin/school/students', {
          method: 'GET',
        });
        const filteredStudents = studentsResponse.filter(
          (s: Student) => s.grade_level === gradeLevel && s.user?.is_active
        );
        setAllStudents(filteredStudents);

        // Загружаем текущих студентов класса
        const classResponse = await apiRequest(`/admin/school/classes/${classId}`, {
          method: 'GET',
        });
        setAssignedStudents(classResponse.students || []);
      } catch (error) {
        notify('Ошибка при загрузке списка студентов', { type: 'error' });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [classId, gradeLevel, notify]);

  const availableStudents = not(allStudents, assignedStudents);
  const leftChecked = intersection(checkedLeft, availableStudents);
  const rightChecked = intersection(checkedRight, assignedStudents);

  const handleToggle = (student: Student, side: 'left' | 'right') => () => {
    if (side === 'left') {
      const currentIndex = checkedLeft.findIndex((s) => s.id === student.id);
      const newChecked = [...checkedLeft];
      if (currentIndex === -1) {
        newChecked.push(student);
      } else {
        newChecked.splice(currentIndex, 1);
      }
      setCheckedLeft(newChecked);
    } else {
      const currentIndex = checkedRight.findIndex((s) => s.id === student.id);
      const newChecked = [...checkedRight];
      if (currentIndex === -1) {
        newChecked.push(student);
      } else {
        newChecked.splice(currentIndex, 1);
      }
      setCheckedRight(newChecked);
    }
  };

  const handleAddStudents = async () => {
    if (leftChecked.length === 0) return;

    try {
      await apiRequest(`/admin/school/classes/${classId}/students`, {
        method: 'POST',
        body: JSON.stringify({ student_ids: leftChecked.map((s) => s.id) }),
      });

      setAssignedStudents([...assignedStudents, ...leftChecked]);
      setCheckedLeft(not(checkedLeft, leftChecked));
      notify(`${leftChecked.length} ученик(ов) добавлены в класс`, { type: 'success' });
      refresh();
    } catch (error) {
      notify('Ошибка при добавлении учеников', { type: 'error' });
    }
  };

  const handleRemoveStudents = async () => {
    if (rightChecked.length === 0) return;

    try {
      await Promise.all(
        rightChecked.map((s) =>
          apiRequest(`/admin/school/classes/${classId}/students/${s.id}`, {
            method: 'DELETE',
          })
        )
      );

      setAssignedStudents(not(assignedStudents, rightChecked));
      setCheckedRight(not(checkedRight, rightChecked));
      notify(`${rightChecked.length} ученик(ов) удалены из класса`, { type: 'success' });
      refresh();
    } catch (error) {
      notify('Ошибка при удалении учеников', { type: 'error' });
    }
  };

  const customList = (title: string, items: Student[], side: 'left' | 'right') => {
    const checked = side === 'left' ? checkedLeft : checkedRight;

    return (
      <Card sx={{ minHeight: 300, maxHeight: 500, overflow: 'auto' }}>
        <CardHeader
          sx={{ px: 2, py: 1 }}
          title={`${title} (${items.length})`}
          titleTypographyProps={{ variant: 'subtitle2' }}
        />
        <Divider />
        <List dense component="div" role="list">
          {items.map((student) => {
            const labelId = `transfer-list-item-${student.id}-label`;
            const fullName = [
              student.user?.last_name,
              student.user?.first_name,
              student.user?.middle_name,
            ]
              .filter(Boolean)
              .join(' ');

            return (
              <ListItem key={student.id} role="listitem" disablePadding>
                <ListItemButton onClick={handleToggle(student, side)}>
                  <ListItemIcon>
                    <Checkbox
                      checked={checked.some((s) => s.id === student.id)}
                      tabIndex={-1}
                      disableRipple
                      inputProps={{
                        'aria-labelledby': labelId,
                      }}
                    />
                  </ListItemIcon>
                  <ListItemText
                    id={labelId}
                    primary={fullName || 'Неизвестно'}
                    secondary={`Код: ${student.student_code}`}
                  />
                </ListItemButton>
              </ListItem>
            );
          })}
        </List>
      </Card>
    );
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Grid container spacing={2} justifyContent="center" alignItems="center">
      <Grid size={5}>
        {customList('Доступные ученики', availableStudents, 'left')}
      </Grid>
      <Grid size={2}>
        <Grid container direction="column" alignItems="center">
          <Button
            sx={{ my: 0.5 }}
            variant="outlined"
            size="small"
            onClick={handleAddStudents}
            disabled={leftChecked.length === 0}
            aria-label="move selected right"
          >
            <ChevronRightIcon />
          </Button>
          <Button
            sx={{ my: 0.5 }}
            variant="outlined"
            size="small"
            onClick={handleRemoveStudents}
            disabled={rightChecked.length === 0}
            aria-label="move selected left"
          >
            <ChevronLeftIcon />
          </Button>
        </Grid>
      </Grid>
      <Grid size={5}>
        {customList('Ученики класса', assignedStudents, 'right')}
      </Grid>
    </Grid>
  );
};

/**
 * Компонент Transfer List для управления учителями класса
 */
const TeachersTransferList: React.FC<{ classId: number }> = ({ classId }) => {
  const notify = useNotify();
  const refresh = useRefresh();
  const [loading, setLoading] = useState(true);
  const [allTeachers, setAllTeachers] = useState<Teacher[]>([]);
  const [assignedTeachers, setAssignedTeachers] = useState<Teacher[]>([]);
  const [checkedLeft, setCheckedLeft] = useState<Teacher[]>([]);
  const [checkedRight, setCheckedRight] = useState<Teacher[]>([]);

  // Загрузка данных
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Загружаем всех учителей школы
        const teachersResponse = await apiRequest('/admin/school/teachers', {
          method: 'GET',
        });
        const activeTeachers = teachersResponse.filter((t: Teacher) => t.user?.is_active);
        setAllTeachers(activeTeachers);

        // Загружаем текущих учителей класса
        const classResponse = await apiRequest(`/admin/school/classes/${classId}`, {
          method: 'GET',
        });
        setAssignedTeachers(classResponse.teachers || []);
      } catch (error) {
        notify('Ошибка при загрузке списка учителей', { type: 'error' });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [classId, notify]);

  const availableTeachers = not(allTeachers, assignedTeachers);
  const leftChecked = intersection(checkedLeft, availableTeachers);
  const rightChecked = intersection(checkedRight, assignedTeachers);

  const handleToggle = (teacher: Teacher, side: 'left' | 'right') => () => {
    if (side === 'left') {
      const currentIndex = checkedLeft.findIndex((t) => t.id === teacher.id);
      const newChecked = [...checkedLeft];
      if (currentIndex === -1) {
        newChecked.push(teacher);
      } else {
        newChecked.splice(currentIndex, 1);
      }
      setCheckedLeft(newChecked);
    } else {
      const currentIndex = checkedRight.findIndex((t) => t.id === teacher.id);
      const newChecked = [...checkedRight];
      if (currentIndex === -1) {
        newChecked.push(teacher);
      } else {
        newChecked.splice(currentIndex, 1);
      }
      setCheckedRight(newChecked);
    }
  };

  const handleAddTeachers = async () => {
    if (leftChecked.length === 0) return;

    try {
      await apiRequest(`/admin/school/classes/${classId}/teachers`, {
        method: 'POST',
        body: JSON.stringify({ teacher_ids: leftChecked.map((t) => t.id) }),
      });

      setAssignedTeachers([...assignedTeachers, ...leftChecked]);
      setCheckedLeft(not(checkedLeft, leftChecked));
      notify(`${leftChecked.length} учител(ей) добавлены в класс`, { type: 'success' });
      refresh();
    } catch (error) {
      notify('Ошибка при добавлении учителей', { type: 'error' });
    }
  };

  const handleRemoveTeachers = async () => {
    if (rightChecked.length === 0) return;

    try {
      await Promise.all(
        rightChecked.map((t) =>
          apiRequest(`/admin/school/classes/${classId}/teachers/${t.id}`, {
            method: 'DELETE',
          })
        )
      );

      setAssignedTeachers(not(assignedTeachers, rightChecked));
      setCheckedRight(not(checkedRight, rightChecked));
      notify(`${rightChecked.length} учител(ей) удалены из класса`, { type: 'success' });
      refresh();
    } catch (error) {
      notify('Ошибка при удалении учителей', { type: 'error' });
    }
  };

  const customList = (title: string, items: Teacher[], side: 'left' | 'right') => {
    const checked = side === 'left' ? checkedLeft : checkedRight;

    return (
      <Card sx={{ minHeight: 300, maxHeight: 500, overflow: 'auto' }}>
        <CardHeader
          sx={{ px: 2, py: 1 }}
          title={`${title} (${items.length})`}
          titleTypographyProps={{ variant: 'subtitle2' }}
        />
        <Divider />
        <List dense component="div" role="list">
          {items.map((teacher) => {
            const labelId = `transfer-list-item-${teacher.id}-label`;
            const fullName = [
              teacher.user?.last_name,
              teacher.user?.first_name,
              teacher.user?.middle_name,
            ]
              .filter(Boolean)
              .join(' ');

            return (
              <ListItem key={teacher.id} role="listitem" disablePadding>
                <ListItemButton onClick={handleToggle(teacher, side)}>
                  <ListItemIcon>
                    <Checkbox
                      checked={checked.some((t) => t.id === teacher.id)}
                      tabIndex={-1}
                      disableRipple
                      inputProps={{
                        'aria-labelledby': labelId,
                      }}
                    />
                  </ListItemIcon>
                  <ListItemText
                    id={labelId}
                    primary={fullName || 'Неизвестно'}
                    secondary={`Предмет: ${teacher.subject || '-'}`}
                  />
                </ListItemButton>
              </ListItem>
            );
          })}
        </List>
      </Card>
    );
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Grid container spacing={2} justifyContent="center" alignItems="center">
      <Grid size={5}>
        {customList('Доступные учителя', availableTeachers, 'left')}
      </Grid>
      <Grid size={2}>
        <Grid container direction="column" alignItems="center">
          <Button
            sx={{ my: 0.5 }}
            variant="outlined"
            size="small"
            onClick={handleAddTeachers}
            disabled={leftChecked.length === 0}
            aria-label="move selected right"
          >
            <ChevronRightIcon />
          </Button>
          <Button
            sx={{ my: 0.5 }}
            variant="outlined"
            size="small"
            onClick={handleRemoveTeachers}
            disabled={rightChecked.length === 0}
            aria-label="move selected left"
          >
            <ChevronLeftIcon />
          </Button>
        </Grid>
      </Grid>
      <Grid size={5}>
        {customList('Учителя класса', assignedTeachers, 'right')}
      </Grid>
    </Grid>
  );
};

/**
 * Обертка для Transfer List компонентов с доступом к record
 */
const TransferListsWrapper = () => {
  const record = useRecordContext<SchoolClass>();

  if (!record) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <>
      {/* Секция: Ученики */}
      <Box sx={{ width: '100%', mt: 4, mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Ученики класса
        </Typography>
        <Divider sx={{ mb: 2 }} />
      </Box>
      <StudentsTransferList classId={record.id} gradeLevel={record.grade_level} />

      {/* Секция: Учителя */}
      <Box sx={{ width: '100%', mt: 4, mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Учителя класса
        </Typography>
        <Divider sx={{ mb: 2 }} />
      </Box>
      <TeachersTransferList classId={record.id} />
    </>
  );
};

/**
 * Компонент редактирования класса
 *
 * Форма содержит три секции:
 * 1. Основная информация (name, grade_level, academic_year)
 * 2. Управление учениками (Transfer List для добавления/удаления)
 * 3. Управление учителями (Transfer List для добавления/удаления)
 */
export const ClassEdit = () => {
  return (
    <Edit redirect="show" title="Редактировать класс" mutationMode="pessimistic">
      <SimpleForm>
        {/* Секция 1: Основная информация */}
        <Box sx={{ width: '100%', mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            Основная информация
          </Typography>
          <Divider sx={{ mb: 2 }} />
        </Box>

        <TextInput
          source="code"
          label="Код класса"
          disabled
          fullWidth
          helperText="Код класса нельзя изменить"
        />

        <TextInput
          source="name"
          label="Название класса"
          validate={validateName}
          fullWidth
          helperText="Например: 7А, 8Б математика, 10 профиль физмат"
        />

        <SelectInput
          source="grade_level"
          label="Класс"
          choices={gradeLevelChoices}
          validate={validateGradeLevel}
          fullWidth
          helperText="Класс обучения (7-11)"
        />

        <TextInput
          source="academic_year"
          label="Учебный год"
          validate={validateAcademicYear}
          fullWidth
          helperText="Формат: YYYY/YYYY (например, 2024/2025)"
        />

        {/* Секции 2-3: Transfer Lists для студентов и учителей */}
        <TransferListsWrapper />
      </SimpleForm>
    </Edit>
  );
};
