import {
  List,
  Datagrid,
  TextField,
  DateField,
  FunctionField,
  SearchInput,
  SelectInput,
  TextInput,
  CreateButton,
  TopToolbar,
  useNotify,
  useRefresh,
  useUnselectAll,
  Button,
  NumberField,
} from 'react-admin';
import type { Identifier } from 'react-admin';
import DeleteIcon from '@mui/icons-material/Delete';
import type { SchoolClass } from '../../types';
import { apiRequest } from '../../providers/dataProvider';

/**
 * Фильтры для списка классов
 * - Поиск по названию, коду
 * - Фильтр по классу (grade_level: 7-11)
 * - Фильтр по учебному году (academic_year)
 */
const classFilters = [
  <SearchInput
    key="q"
    source="q"
    placeholder="Поиск по названию, коду"
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
  <TextInput
    key="academic_year"
    source="academic_year"
    label="Учебный год"
    placeholder="2024/2025"
  />,
];

/**
 * Toolbar сверху списка с кнопкой создания
 */
const ListActions = () => (
  <TopToolbar>
    <CreateButton label="Добавить класс" />
  </TopToolbar>
);

/**
 * Кнопка для удаления нескольких классов (soft delete)
 * DELETE /admin/school/classes/{id}
 */
const BulkDeleteButton = ({ selectedIds = [] }: { selectedIds?: Identifier[] }) => {
  const notify = useNotify();
  const refresh = useRefresh();
  const unselectAll = useUnselectAll('classes');

  const handleDelete = async () => {
    if (!window.confirm(`Вы уверены, что хотите удалить ${selectedIds.length} класс(ов)?`)) {
      return;
    }

    try {
      await Promise.all(
        selectedIds.map((id: Identifier) =>
          apiRequest(`/admin/school/classes/${id}`, { method: 'DELETE' })
        )
      );
      notify(`${selectedIds.length} класс(ов) удалены`, { type: 'success' });
      refresh();
      unselectAll();
    } catch (error) {
      notify('Ошибка при удалении классов', { type: 'error' });
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
 * Кастомное поле для отображения количества учеников
 */
const StudentsCountField = () => {
  return (
    <FunctionField
      label="Учеников"
      render={(record: SchoolClass) => record.students_count || 0}
      sortable={false}
    />
  );
};

/**
 * Кастомное поле для отображения количества учителей
 */
const TeachersCountField = () => {
  return (
    <FunctionField
      label="Учителей"
      render={(record: SchoolClass) => record.teachers_count || 0}
      sortable={false}
    />
  );
};

/**
 * Компонент списка классов
 *
 * Отображает таблицу всех классов школы с:
 * - Колонками: ID, код, название, класс, учебный год, кол-во учеников, кол-во учителей, дата создания
 * - Фильтрами: поиск, класс (grade_level), учебный год
 * - Bulk actions: удаление нескольких классов
 * - Кликабельными строками для перехода к детальному просмотру
 * - Сортировкой по всем колонкам
 */
export const ClassList = () => {
  return (
    <List
      filters={classFilters}
      actions={<ListActions />}
      sort={{ field: 'created_at', order: 'DESC' }}
      perPage={25}
      title="Классы"
    >
      <Datagrid
        rowClick="show"
        bulkActionButtons={
          <>
            <BulkDeleteButton />
          </>
        }
      >
        <TextField source="id" label="ID" sortable />
        <TextField source="code" label="Код класса" sortable />
        <TextField source="name" label="Название" sortable />
        <NumberField source="grade_level" label="Класс" sortable />
        <TextField source="academic_year" label="Учебный год" sortable />
        <StudentsCountField />
        <TeachersCountField />
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
