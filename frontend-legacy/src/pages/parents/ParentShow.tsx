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
import type { Parent, StudentBrief } from '../../types';

/**
 * Кастомное поле для отображения статуса родителя
 */
const StatusField = () => {
  return (
    <FunctionField
      label="Статус"
      render={(record: Parent) => (
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
 * Кастомное поле для отображения полного имени родителя
 */
const FullNameField = () => {
  return (
    <FunctionField
      label="ФИО"
      render={(record: Parent) => {
        const { first_name, last_name, middle_name } = record.user || {};
        return [last_name, first_name, middle_name].filter(Boolean).join(' ') || '-';
      }}
    />
  );
};

/**
 * Компонент для вкладки "Дети"
 * Отображает список детей родителя
 */
const ChildrenTab = () => {
  const record = useRecordContext<Parent>();

  if (!record?.children || record.children.length === 0) {
    return (
      <Alert severity="info" sx={{ m: 2 }}>
        У родителя нет привязанных детей
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Дети ({record.children.length})
      </Typography>
      <List>
        {record.children.map((child: StudentBrief) => {
          // Формируем полное имя из user данных
          const fullName = [
            child.user?.last_name,
            child.user?.first_name,
            child.user?.middle_name,
          ]
            .filter(Boolean)
            .join(' ');

          return (
            <ListItem key={child.id} divider>
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="subtitle1">
                      {fullName || 'Без имени'}
                    </Typography>
                    <Chip
                      label={child.user?.is_active ? 'Активен' : 'Деактивирован'}
                      color={child.user?.is_active ? 'success' : 'default'}
                      size="small"
                    />
                  </Box>
                }
                secondary={
                  <>
                    Код: {child.student_code} • {child.grade_level} класс
                    {child.user?.email && ` • Email: ${child.user.email}`}
                  </>
                }
              />
            </ListItem>
          );
        })}
      </List>
    </Box>
  );
};

/**
 * Компонент детального просмотра родителя
 *
 * Отображает информацию о родителе с использованием TabbedShowLayout:
 * - Вкладка "Информация": все поля User (нет специфичных полей Parent)
 * - Вкладка "Дети": список детей с полной информацией
 */
export const ParentShow = () => (
  <Show title="Просмотр родителя">
    <TabbedShowLayout>
      {/* Вкладка 1: Информация о родителе */}
      <Tab label="Информация">
        <TextField source="id" label="ID" />
        <FullNameField />
        <StatusField />

        {/* User данные */}
        <FunctionField
          label="Email"
          render={(record: Parent) => record.user?.email || '-'}
        />
        <FunctionField
          label="Телефон"
          render={(record: Parent) => record.user?.phone || '-'}
        />
        <FunctionField
          label="Имя"
          render={(record: Parent) => record.user?.first_name || '-'}
        />
        <FunctionField
          label="Фамилия"
          render={(record: Parent) => record.user?.last_name || '-'}
        />
        <FunctionField
          label="Отчество"
          render={(record: Parent) => record.user?.middle_name || '-'}
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

      {/* Вкладка 2: Дети */}
      <Tab label="Дети" path="children">
        <ChildrenTab />
      </Tab>
    </TabbedShowLayout>
  </Show>
);
