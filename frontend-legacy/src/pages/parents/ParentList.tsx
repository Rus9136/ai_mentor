import {
  List,
  Datagrid,
  TextField,
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
import PersonOffIcon from '@mui/icons-material/PersonOff';
import DeleteIcon from '@mui/icons-material/Delete';
import type { Parent } from '../../types';
import { apiRequest } from '../../providers/dataProvider';

/**
 * Фильтры для списка родителей
 * - Поиск по имени, email
 * - Фильтр по статусу активности (is_active)
 */
const parentFilters = [
  <SearchInput
    key="q"
    source="q"
    placeholder="Поиск по имени, email"
    alwaysOn
  />,
  <SelectInput
    key="is_active"
    source="is_active"
    label="Статус"
    choices={[
      { id: true, name: 'Активные' },
      { id: false, name: 'Деактивированные' },
    ]}
  />,
];

/**
 * Toolbar сверху списка с кнопкой создания
 */
const ListActions = () => (
  <TopToolbar>
    <CreateButton label="Добавить родителя" />
  </TopToolbar>
);

/**
 * Кнопка для деактивации нескольких родителей
 * Деактивирует user.is_active через PATCH /admin/school/parents/{id}/deactivate
 */
const BulkDeactivateButton = ({ selectedIds = [] }: { selectedIds?: Identifier[] }) => {
  const notify = useNotify();
  const refresh = useRefresh();
  const unselectAll = useUnselectAll('parents');

  const handleDeactivate = async () => {
    try {
      await Promise.all(
        selectedIds.map((id: Identifier) =>
          apiRequest(`/admin/school/parents/${id}/deactivate`, { method: 'PATCH' })
        )
      );
      notify(`${selectedIds.length} родител(ей) деактивированы`, { type: 'success' });
      refresh();
      unselectAll();
    } catch (error) {
      notify('Ошибка при деактивации родителей', { type: 'error' });
    }
  };

  return (
    <Button
      label="Деактивировать"
      onClick={handleDeactivate}
      startIcon={<PersonOffIcon />}
    />
  );
};

/**
 * Кнопка для удаления нескольких родителей (soft delete)
 * DELETE /admin/school/parents/{id}
 */
const BulkDeleteButton = ({ selectedIds = [] }: { selectedIds?: Identifier[] }) => {
  const notify = useNotify();
  const refresh = useRefresh();
  const unselectAll = useUnselectAll('parents');

  const handleDelete = async () => {
    if (!window.confirm(`Вы уверены, что хотите удалить ${selectedIds.length} родител(ей)?`)) {
      return;
    }

    try {
      await Promise.all(
        selectedIds.map((id: Identifier) =>
          apiRequest(`/admin/school/parents/${id}`, { method: 'DELETE' })
        )
      );
      notify(`${selectedIds.length} родител(ей) удалены`, { type: 'success' });
      refresh();
      unselectAll();
    } catch (error) {
      notify('Ошибка при удалении родителей', { type: 'error' });
    }
  };

  return (
    <Button
      label="Удалить"
      onClick={handleDelete}
      startIcon={<DeleteIcon />}
    />
  );
};

/**
 * Кастомное поле для отображения статуса родителя
 * Показывает user.is_active в виде цветного badge
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
          sx={{ fontWeight: 500 }}
        />
      )}
      sortBy="user.is_active"
      sortable
    />
  );
};

/**
 * Кастомное поле для отображения полного имени родителя
 * Комбинирует user.last_name, user.first_name, user.middle_name
 */
const FullNameField = () => {
  return (
    <FunctionField
      label="ФИО"
      render={(record: Parent) => {
        const { first_name, last_name, middle_name } = record.user || {};
        return [last_name, first_name, middle_name].filter(Boolean).join(' ');
      }}
      sortBy="user.last_name"
      sortable
    />
  );
};

/**
 * Кастомное поле для отображения email из user
 */
const UserEmailField = () => {
  return (
    <FunctionField
      label="Email"
      render={(record: Parent) => record.user?.email || '-'}
      sortBy="user.email"
      sortable
    />
  );
};

/**
 * Кастомное поле для отображения количества детей
 */
const ChildrenCountField = () => {
  return (
    <FunctionField
      label="Детей"
      render={(record: Parent) => record.children?.length || 0}
      sortable={false}
    />
  );
};

/**
 * Компонент списка родителей
 *
 * Отображает таблицу всех родителей школы с:
 * - Колонками: ID, ФИО, email, количество детей, статус, дата создания
 * - Фильтрами: поиск, статус активности
 * - Bulk actions: деактивация, удаление нескольких родителей
 * - Кликабельными строками для перехода к детальному просмотру
 * - Сортировкой по всем колонкам
 */
export const ParentList = () => {
  return (
    <List
      filters={parentFilters}
      actions={<ListActions />}
      sort={{ field: 'created_at', order: 'DESC' }}
      perPage={25}
      title="Родители"
    >
      <Datagrid
        rowClick="show"
        bulkActionButtons={
          <>
            <BulkDeactivateButton />
            <BulkDeleteButton />
          </>
        }
      >
        <TextField source="id" label="ID" sortable />
        <FullNameField />
        <UserEmailField />
        <ChildrenCountField />
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
