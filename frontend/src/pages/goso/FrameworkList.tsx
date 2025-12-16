import {
  List,
  Datagrid,
  TextField,
  DateField,
  TextInput,
  TopToolbar,
  FilterButton,
  FunctionField,
} from 'react-admin';
import { Chip, Typography, Box } from '@mui/material';
import type { Framework } from '../../types';

/**
 * Фильтры для списка версий ГОСО
 */
const frameworkFilters = [
  <TextInput key="q" source="q" label="Поиск" alwaysOn />,
];

/**
 * Actions для списка
 */
const ListActions = () => (
  <TopToolbar>
    <FilterButton />
  </TopToolbar>
);

/**
 * Рендер функция для отображения статуса
 */
const renderStatus = (record: Framework) => (
  <Chip
    label={record.is_active ? 'Активен' : 'Неактивен'}
    color={record.is_active ? 'success' : 'default'}
    size="small"
  />
);

/**
 * Рендер функция для отображения периода действия
 */
const renderValidity = (record: Framework) => {
  const from = record.valid_from ? new Date(record.valid_from).toLocaleDateString('ru-RU') : '—';
  const to = record.valid_to ? new Date(record.valid_to).toLocaleDateString('ru-RU') : 'по н.в.';

  return (
    <Typography variant="body2">
      {from} — {to}
    </Typography>
  );
};

/**
 * Пустой компонент для случая когда нет данных
 */
const Empty = () => (
  <Box textAlign="center" p={3}>
    <Typography variant="h6" color="textSecondary">
      Нет версий ГОСО
    </Typography>
    <Typography variant="body2" color="textSecondary">
      Версии государственного стандарта образования еще не загружены
    </Typography>
  </Box>
);

/**
 * Список версий ГОСО (Frameworks)
 *
 * Отображает таблицу с версиями государственного стандарта образования.
 * Read-only для SUPER_ADMIN.
 */
export const FrameworkList = () => (
  <List
    title="ГОСО Стандарты"
    filters={frameworkFilters}
    actions={<ListActions />}
    sort={{ field: 'id', order: 'DESC' }}
    perPage={25}
    empty={<Empty />}
  >
    <Datagrid
      rowClick="show"
      bulkActionButtons={false}
      sx={{
        '& .RaDatagrid-row': {
          cursor: 'pointer',
        },
      }}
    >
      <TextField source="id" label="ID" sortable />
      <TextField source="code" label="Код" sortable />
      <TextField source="title_ru" label="Название" sortable />
      <FunctionField label="Период действия" render={renderValidity} />
      <FunctionField label="Статус" render={renderStatus} />
      <DateField
        source="created_at"
        label="Создан"
        locales="ru-RU"
        options={{ year: 'numeric', month: 'short', day: 'numeric' }}
      />
    </Datagrid>
  </List>
);
