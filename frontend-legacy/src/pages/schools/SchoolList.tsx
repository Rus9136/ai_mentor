import {
  List,
  Datagrid,
  TextField,
  EmailField,
  DateField,
  FunctionField,
  SearchInput,
  SelectInput,
  CreateButton,
  TopToolbar,
  useNotify,
  useRefresh,
  useUnselectAll,
  Button,
} from 'react-admin';
import type { Identifier } from 'react-admin';
import { Chip } from '@mui/material';
import BlockIcon from '@mui/icons-material/Block';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import type { School } from '../../types';
import { apiRequest } from '../../providers/dataProvider';

/**
 * Фильтры для списка школ
 * - Поиск по названию и коду
 * - Фильтр по статусу (активные/заблокированные)
 */
const schoolFilters = [
  <SearchInput key="q" source="q" placeholder="Поиск по названию или коду" alwaysOn />,
  <SelectInput
    key="is_active"
    source="is_active"
    label="Статус"
    choices={[
      { id: true, name: 'Активные' },
      { id: false, name: 'Заблокированные' },
    ]}
    alwaysOn
  />,
];

/**
 * Toolbar сверху списка с кнопкой создания
 */
const ListActions = () => (
  <TopToolbar>
    <CreateButton label="Создать школу" />
  </TopToolbar>
);

/**
 * Кнопка для блокировки нескольких школ
 */
const BulkBlockButton = ({ selectedIds = [] }: { selectedIds?: Identifier[] }) => {
  const notify = useNotify();
  const refresh = useRefresh();
  const unselectAll = useUnselectAll('schools');

  const handleBlock = async () => {
    try {
      await Promise.all(
        selectedIds.map((id: Identifier) =>
          apiRequest(`/admin/schools/${id}/block`, { method: 'PATCH' })
        )
      );
      notify(`${selectedIds.length} школ(ы) заблокированы`, { type: 'success' });
      refresh();
      unselectAll();
    } catch (error) {
      notify('Ошибка при блокировке школ', { type: 'error' });
    }
  };

  return (
    <Button
      label="Заблокировать"
      onClick={handleBlock}
      startIcon={<BlockIcon />}
    />
  );
};

/**
 * Кнопка для разблокировки нескольких школ
 */
const BulkUnblockButton = ({ selectedIds = [] }: { selectedIds?: Identifier[] }) => {
  const notify = useNotify();
  const refresh = useRefresh();
  const unselectAll = useUnselectAll('schools');

  const handleUnblock = async () => {
    try {
      await Promise.all(
        selectedIds.map((id: Identifier) =>
          apiRequest(`/admin/schools/${id}/unblock`, { method: 'PATCH' })
        )
      );
      notify(`${selectedIds.length} школ(ы) разблокированы`, { type: 'success' });
      refresh();
      unselectAll();
    } catch (error) {
      notify('Ошибка при разблокировке школ', { type: 'error' });
    }
  };

  return (
    <Button
      label="Разблокировать"
      onClick={handleUnblock}
      startIcon={<CheckCircleIcon />}
    />
  );
};

/**
 * Кастомное поле для отображения статуса школы в виде цветного badge
 */
const StatusField = () => {
  return (
    <FunctionField
      label="Статус"
      render={(record: School) => (
        <Chip
          label={record.is_active ? 'Активна' : 'Заблокирована'}
          color={record.is_active ? 'success' : 'error'}
          size="small"
          sx={{ fontWeight: 500 }}
        />
      )}
      sortBy="is_active"
      sortable
    />
  );
};

/**
 * Компонент списка школ
 *
 * Отображает таблицу всех школ с:
 * - Колонками: название, код, email, статус, дата создания
 * - Фильтрами: поиск по названию/коду, фильтр по статусу
 * - Bulk actions: блокировка/разблокировка нескольких школ
 * - Кликабельными строками для перехода к детальному просмотру
 * - Сортировкой по всем колонкам
 */
export const SchoolList = () => {
  return (
    <List
      filters={schoolFilters}
      actions={<ListActions />}
      sort={{ field: 'created_at', order: 'DESC' }}
      perPage={25}
    >
      <Datagrid
        rowClick="show"
        bulkActionButtons={
          <>
            <BulkBlockButton />
            <BulkUnblockButton />
          </>
        }
      >
        <TextField source="id" label="ID" sortable />
        <TextField source="name" label="Название" sortable />
        <TextField source="code" label="Код" sortable />
        <EmailField source="email" label="Email" sortable />
        <StatusField />
        <DateField
          source="created_at"
          label="Дата создания"
          showTime
          locales="ru-RU"
          sortable
        />
      </Datagrid>
    </List>
  );
};
