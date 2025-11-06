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
  NumberField,
} from 'react-admin';
import type { Identifier } from 'react-admin';
import { Chip } from '@mui/material';
import PersonOffIcon from '@mui/icons-material/PersonOff';
import DeleteIcon from '@mui/icons-material/Delete';
import type { Student } from '../../types';
import { apiRequest } from '../../providers/dataProvider';

/**
 * Фильтры для списка учеников
 * - Поиск по имени, email, коду ученика
 * - Фильтр по классу (grade_level: 7-11)
 * - Фильтр по классу-группе (class_id)
 * - Фильтр по статусу активности (is_active)
 */
const studentFilters = [
  <SearchInput
    key="q"
    source="q"
    placeholder="Поиск по имени, email, коду"
    alwaysOn
  />,
  <SelectInput
    key="grade_level"
    source="grade_level"
    label="Класс"
    choices={[
      { id: 7, name: '7 класс' },
      { id: 8, name: '8 класс' },
      { id: 9, name: '9 класс' },
      { id: 10, name: '10 класс' },
      { id: 11, name: '11 класс' },
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
    <CreateButton label="Добавить ученика" />
  </TopToolbar>
);

/**
 * Кнопка для деактивации нескольких учеников
 * Деактивирует user.is_active через PATCH /admin/school/students/{id}/deactivate
 */
const BulkDeactivateButton = ({ selectedIds = [] }: { selectedIds?: Identifier[] }) => {
  const notify = useNotify();
  const refresh = useRefresh();
  const unselectAll = useUnselectAll('students');

  const handleDeactivate = async () => {
    try {
      await Promise.all(
        selectedIds.map((id: Identifier) =>
          apiRequest(`/admin/school/students/${id}/deactivate`, { method: 'PATCH' })
        )
      );
      notify(`${selectedIds.length} ученик(ов) деактивированы`, { type: 'success' });
      refresh();
      unselectAll();
    } catch (error) {
      notify('Ошибка при деактивации учеников', { type: 'error' });
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
 * Кнопка для удаления нескольких учеников (soft delete)
 * DELETE /admin/school/students/{id}
 */
const BulkDeleteButton = ({ selectedIds = [] }: { selectedIds?: Identifier[] }) => {
  const notify = useNotify();
  const refresh = useRefresh();
  const unselectAll = useUnselectAll('students');

  const handleDelete = async () => {
    if (!window.confirm(`Вы уверены, что хотите удалить ${selectedIds.length} ученик(ов)?`)) {
      return;
    }

    try {
      await Promise.all(
        selectedIds.map((id: Identifier) =>
          apiRequest(`/admin/school/students/${id}`, { method: 'DELETE' })
        )
      );
      notify(`${selectedIds.length} ученик(ов) удалены`, { type: 'success' });
      refresh();
      unselectAll();
    } catch (error) {
      notify('Ошибка при удалении учеников', { type: 'error' });
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
 * Кастомное поле для отображения статуса ученика
 * Показывает user.is_active в виде цветного badge
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
          sx={{ fontWeight: 500 }}
        />
      )}
      sortBy="user.is_active"
      sortable
    />
  );
};

/**
 * Кастомное поле для отображения полного имени ученика
 * Комбинирует user.last_name, user.first_name, user.middle_name
 */
const FullNameField = () => {
  return (
    <FunctionField
      label="ФИО"
      render={(record: Student) => {
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
      render={(record: Student) => record.user?.email || '-'}
      sortBy="user.email"
      sortable
    />
  );
};

/**
 * Компонент списка учеников
 *
 * Отображает таблицу всех учеников школы с:
 * - Колонками: ID, код ученика, ФИО, email, класс, статус, дата создания
 * - Фильтрами: поиск, класс, класс-группа, статус активности
 * - Bulk actions: деактивация, удаление нескольких учеников
 * - Кликабельными строками для перехода к детальному просмотру
 * - Сортировкой по всем колонкам
 */
export const StudentList = () => {
  return (
    <List
      filters={studentFilters}
      actions={<ListActions />}
      sort={{ field: 'created_at', order: 'DESC' }}
      perPage={25}
      title="Ученики"
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
        <TextField source="student_code" label="Код ученика" sortable />
        <FullNameField />
        <UserEmailField />
        <NumberField source="grade_level" label="Класс" sortable />
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
