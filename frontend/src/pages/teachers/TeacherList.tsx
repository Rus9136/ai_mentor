import {
  List,
  Datagrid,
  TextField,
  DateField,
  FunctionField,
  SearchInput,
  SelectInput,
  ReferenceInput,
  AutocompleteInput,
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
import type { Teacher } from '../../types';
import { apiRequest } from '../../providers/dataProvider';

/**
 * Фильтры для списка учителей
 * - Поиск по имени, email, коду учителя
 * - Фильтр по предмету
 * - Фильтр по классу-группе (class_id)
 * - Фильтр по статусу активности (is_active)
 */
const teacherFilters = [
  <SearchInput
    key="q"
    source="q"
    placeholder="Поиск по имени, email, коду"
    alwaysOn
  />,
  <SelectInput
    key="subject"
    source="subject"
    label="Предмет"
    choices={[
      { id: 'Математика', name: 'Математика' },
      { id: 'Алгебра', name: 'Алгебра' },
      { id: 'Геометрия', name: 'Геометрия' },
      { id: 'Физика', name: 'Физика' },
      { id: 'Химия', name: 'Химия' },
      { id: 'Биология', name: 'Биология' },
      { id: 'География', name: 'География' },
      { id: 'История', name: 'История' },
      { id: 'Литература', name: 'Литература' },
      { id: 'Русский язык', name: 'Русский язык' },
      { id: 'Английский язык', name: 'Английский язык' },
      { id: 'Информатика', name: 'Информатика' },
    ]}
  />,
  <ReferenceInput
    key="class_id"
    source="class_id"
    reference="classes"
    label="Класс-группа"
  >
    <AutocompleteInput
      optionText={(record) => `${record.name} (${record.code})`}
      filterToQuery={(searchText) => ({ q: searchText })}
    />
  </ReferenceInput>,
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
    <CreateButton label="Добавить учителя" />
  </TopToolbar>
);

/**
 * Кнопка для деактивации нескольких учителей
 * Деактивирует user.is_active через PATCH /admin/school/teachers/{id}/deactivate
 */
const BulkDeactivateButton = ({ selectedIds = [] }: { selectedIds?: Identifier[] }) => {
  const notify = useNotify();
  const refresh = useRefresh();
  const unselectAll = useUnselectAll('teachers');

  const handleDeactivate = async () => {
    try {
      await Promise.all(
        selectedIds.map((id: Identifier) =>
          apiRequest(`/admin/school/teachers/${id}/deactivate`, { method: 'PATCH' })
        )
      );
      notify(`${selectedIds.length} учител(ей) деактивированы`, { type: 'success' });
      refresh();
      unselectAll();
    } catch (error) {
      notify('Ошибка при деактивации учителей', { type: 'error' });
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
 * Кнопка для удаления нескольких учителей (soft delete)
 * DELETE /admin/school/teachers/{id}
 */
const BulkDeleteButton = ({ selectedIds = [] }: { selectedIds?: Identifier[] }) => {
  const notify = useNotify();
  const refresh = useRefresh();
  const unselectAll = useUnselectAll('teachers');

  const handleDelete = async () => {
    if (!window.confirm(`Вы уверены, что хотите удалить ${selectedIds.length} учител(ей)?`)) {
      return;
    }

    try {
      await Promise.all(
        selectedIds.map((id: Identifier) =>
          apiRequest(`/admin/school/teachers/${id}`, { method: 'DELETE' })
        )
      );
      notify(`${selectedIds.length} учител(ей) удалены`, { type: 'success' });
      refresh();
      unselectAll();
    } catch (error) {
      notify('Ошибка при удалении учителей', { type: 'error' });
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
 * Кастомное поле для отображения статуса учителя
 * Показывает user.is_active в виде цветного badge
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
          sx={{ fontWeight: 500 }}
        />
      )}
      sortBy="user.is_active"
      sortable
    />
  );
};

/**
 * Кастомное поле для отображения полного имени учителя
 * Комбинирует user.last_name, user.first_name, user.middle_name
 */
const FullNameField = () => {
  return (
    <FunctionField
      label="ФИО"
      render={(record: Teacher) => {
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
      render={(record: Teacher) => record.user?.email || '-'}
      sortBy="user.email"
      sortable
    />
  );
};

/**
 * Компонент списка учителей
 *
 * Отображает таблицу всех учителей школы с:
 * - Колонками: ID, код учителя, ФИО, email, предмет, статус, дата создания
 * - Фильтрами: поиск, предмет, класс-группа, статус активности
 * - Bulk actions: деактивация, удаление нескольких учителей
 * - Кликабельными строками для перехода к детальному просмотру
 * - Сортировкой по всем колонкам
 */
export const TeacherList = () => {
  return (
    <List
      filters={teacherFilters}
      actions={<ListActions />}
      sort={{ field: 'created_at', order: 'DESC' }}
      perPage={25}
      title="Учителя"
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
        <TextField source="teacher_code" label="Код учителя" sortable />
        <FullNameField />
        <UserEmailField />
        <TextField source="subject" label="Предмет" sortable />
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
