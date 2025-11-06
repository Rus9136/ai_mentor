import {
  Show,
  TextField,
  DateField,
  FunctionField,
  TabbedShowLayout,
  Tab,
  useRecordContext,
} from 'react-admin';
import {
  Chip,
  List,
  ListItem,
  ListItemText,
  Typography,
  Alert,
  Box,
} from '@mui/material';
import type { Teacher, SchoolClassBrief } from '../../types';

/**
 * Кастомное поле для отображения статуса учителя
 */
const StatusField = () => {
  return (
    <FunctionField
      label="Статус"
      render={(record: Teacher) => (
        <Chip
          label={record.user?.is_active ? 'Активен' : 'Деактивирован'}
          color={record.user?.is_active ? 'success' : 'default'}
          size="small"
        />
      )}
    />
  );
};

/**
 * Кастомное поле для отображения полного имени учителя
 */
const FullNameField = () => {
  return (
    <FunctionField
      label="ФИО"
      render={(record: Teacher) => {
        const { first_name, last_name, middle_name } = record.user || {};
        return [last_name, first_name, middle_name].filter(Boolean).join(' ') || '-';
      }}
    />
  );
};

/**
 * Компонент для вкладки "Классы"
 * Отображает список классов-групп, которые ведет учитель
 */
const ClassesTab = () => {
  const record = useRecordContext<Teacher>();

  if (!record?.classes || record.classes.length === 0) {
    return (
      <Alert severity="info" sx={{ m: 2 }}>
        Учитель не ведет ни одного класса-группы
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Классы-группы ({record.classes.length})
      </Typography>
      <List>
        {record.classes.map((classItem: SchoolClassBrief) => (
          <ListItem key={classItem.id} divider>
            <ListItemText
              primary={
                <Typography variant="subtitle1">
                  {classItem.name} ({classItem.code})
                </Typography>
              }
              secondary={`${classItem.grade_level} класс • Учебный год: ${classItem.academic_year}`}
            />
          </ListItem>
        ))}
      </List>
    </Box>
  );
};

/**
 * Компонент детального просмотра учителя
 *
 * Отображает информацию об учителе с использованием TabbedShowLayout:
 * - Вкладка "Информация": все поля Teacher + nested User
 * - Вкладка "Классы": список классов-групп, которые ведет учитель
 */
export const TeacherShow = () => (
  <Show title="Просмотр учителя">
    <TabbedShowLayout>
      {/* Вкладка 1: Информация об учителе */}
      <Tab label="Информация">
        <TextField source="id" label="ID" />
        <TextField source="teacher_code" label="Код учителя" />
        <FullNameField />
        <TextField source="subject" label="Предмет" />
        <StatusField />

        {/* User данные */}
        <FunctionField
          label="Email"
          render={(record: Teacher) => record.user?.email || '-'}
        />
        <FunctionField
          label="Телефон"
          render={(record: Teacher) => record.user?.phone || '-'}
        />
        <FunctionField
          label="Имя"
          render={(record: Teacher) => record.user?.first_name || '-'}
        />
        <FunctionField
          label="Фамилия"
          render={(record: Teacher) => record.user?.last_name || '-'}
        />
        <FunctionField
          label="Отчество"
          render={(record: Teacher) => record.user?.middle_name || '-'}
        />

        {/* Teacher специфичные поля */}
        <FunctionField
          label="Биография"
          render={(record: Teacher) => (
            <Box sx={{ whiteSpace: 'pre-wrap' }}>
              {record.bio || '-'}
            </Box>
          )}
        />

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

      {/* Вкладка 2: Классы-группы */}
      <Tab label="Классы" path="classes">
        <ClassesTab />
      </Tab>
    </TabbedShowLayout>
  </Show>
);
