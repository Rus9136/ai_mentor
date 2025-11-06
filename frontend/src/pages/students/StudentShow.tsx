import {
  Show,
  TextField,
  DateField,
  FunctionField,
  TabbedShowLayout,
  Tab,
  useRecordContext,
  NumberField,
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
import type { Student, SchoolClassBrief } from '../../types';

/**
 * Кастомное поле для отображения статуса ученика
 */
const StatusField = () => {
  return (
    <FunctionField
      label="Статус"
      render={(record: Student) => (
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
 * Кастомное поле для отображения полного имени ученика
 */
const FullNameField = () => {
  return (
    <FunctionField
      label="ФИО"
      render={(record: Student) => {
        const { first_name, last_name, middle_name } = record.user || {};
        return [last_name, first_name, middle_name].filter(Boolean).join(' ') || '-';
      }}
    />
  );
};

/**
 * Компонент для вкладки "Классы"
 * Отображает список классов-групп, в которых состоит ученик
 */
const ClassesTab = () => {
  const record = useRecordContext<Student>();

  if (!record?.classes || record.classes.length === 0) {
    return (
      <Alert severity="info" sx={{ m: 2 }}>
        Ученик не состоит ни в одном классе-группе
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
 * Компонент детального просмотра ученика
 *
 * Отображает информацию о ученике с использованием TabbedShowLayout:
 * - Вкладка "Информация": все поля Student + nested User
 * - Вкладка "Классы": список классов-групп, в которых состоит ученик
 */
export const StudentShow = () => (
  <Show title="Просмотр ученика">
    <TabbedShowLayout>
      {/* Вкладка 1: Информация о ученике */}
      <Tab label="Информация">
        <TextField source="id" label="ID" />
        <TextField source="student_code" label="Код ученика" />
        <FullNameField />
        <NumberField source="grade_level" label="Класс" />
        <StatusField />

        {/* User данные */}
        <FunctionField
          label="Email"
          render={(record: Student) => record.user?.email || '-'}
        />
        <FunctionField
          label="Телефон"
          render={(record: Student) => record.user?.phone || '-'}
        />
        <FunctionField
          label="Имя"
          render={(record: Student) => record.user?.first_name || '-'}
        />
        <FunctionField
          label="Фамилия"
          render={(record: Student) => record.user?.last_name || '-'}
        />
        <FunctionField
          label="Отчество"
          render={(record: Student) => record.user?.middle_name || '-'}
        />

        {/* Student специфичные поля */}
        <DateField
          source="birth_date"
          label="Дата рождения"
          locales="ru-RU"
          emptyText="-"
        />
        <DateField
          source="enrollment_date"
          label="Дата зачисления"
          locales="ru-RU"
          emptyText="-"
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
