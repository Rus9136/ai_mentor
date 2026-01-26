import {
  Show,
  TextField,
  DateField,
  TabbedShowLayout,
  Tab,
  useRecordContext,
  NumberField,
} from 'react-admin';
import {
  List,
  ListItem,
  ListItemText,
  Typography,
  Alert,
  Box,
} from '@mui/material';
import type { SchoolClass, Student, Teacher } from '../../types';

/**
 * Компонент для вкладки "Ученики"
 * Отображает список учеников класса с их ФИО, кодом и классом
 */
const StudentsTab = () => {
  const record = useRecordContext<SchoolClass>();

  if (!record?.students || record.students.length === 0) {
    return (
      <Alert severity="info" sx={{ m: 2 }}>
        В классе пока нет учеников
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Ученики ({record.students.length})
      </Typography>
      <List>
        {record.students.map((student: Student) => {
          const fullName = [
            student.user?.last_name,
            student.user?.first_name,
            student.user?.middle_name,
          ]
            .filter(Boolean)
            .join(' ');

          return (
            <ListItem key={student.id} divider>
              <ListItemText
                primary={
                  <Typography variant="subtitle1">
                    {fullName || 'Неизвестно'}
                  </Typography>
                }
                secondary={`Код: ${student.student_code} • ${student.grade_level} класс • Email: ${student.user?.email || '-'}`}
              />
            </ListItem>
          );
        })}
      </List>
    </Box>
  );
};

/**
 * Компонент для вкладки "Учителя"
 * Отображает список учителей класса с их ФИО, кодом и предметом
 */
const TeachersTab = () => {
  const record = useRecordContext<SchoolClass>();

  if (!record?.teachers || record.teachers.length === 0) {
    return (
      <Alert severity="info" sx={{ m: 2 }}>
        В классе пока нет учителей
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Учителя ({record.teachers.length})
      </Typography>
      <List>
        {record.teachers.map((teacher: Teacher) => {
          const fullName = [
            teacher.user?.last_name,
            teacher.user?.first_name,
            teacher.user?.middle_name,
          ]
            .filter(Boolean)
            .join(' ');

          return (
            <ListItem key={teacher.id} divider>
              <ListItemText
                primary={
                  <Typography variant="subtitle1">
                    {fullName || 'Неизвестно'}
                  </Typography>
                }
                secondary={`Код: ${teacher.teacher_code} • Предмет: ${teacher.subject || '-'} • Email: ${teacher.user?.email || '-'}`}
              />
            </ListItem>
          );
        })}
      </List>
    </Box>
  );
};

/**
 * Компонент детального просмотра класса
 *
 * Отображает информацию о классе с использованием TabbedShowLayout:
 * - Вкладка "Информация": базовые поля класса (id, code, name, grade_level, academic_year, timestamps)
 * - Вкладка "Ученики": список учеников класса с детальной информацией
 * - Вкладка "Учителя": список учителей класса с детальной информацией
 */
export const ClassShow = () => (
  <Show title="Просмотр класса">
    <TabbedShowLayout>
      {/* Вкладка 1: Информация о классе */}
      <Tab label="Информация">
        <TextField source="id" label="ID" />
        <TextField source="code" label="Код класса" />
        <TextField source="name" label="Название" />
        <NumberField source="grade_level" label="Класс" />
        <TextField source="academic_year" label="Учебный год" />

        {/* Счетчики */}
        <NumberField source="students_count" label="Количество учеников" emptyText="0" />
        <NumberField source="teachers_count" label="Количество учителей" emptyText="0" />

        {/* Timestamps */}
        <DateField
          source="created_at"
          label="Дата создания"
          showTime
          locales="ru-RU"
        />
        <DateField
          source="updated_at"
          label="Обновлено"
          showTime
          locales="ru-RU"
        />
      </Tab>

      {/* Вкладка 2: Ученики */}
      <Tab label="Ученики" path="students">
        <StudentsTab />
      </Tab>

      {/* Вкладка 3: Учителя */}
      <Tab label="Учителя" path="teachers">
        <TeachersTab />
      </Tab>
    </TabbedShowLayout>
  </Show>
);
