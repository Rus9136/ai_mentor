import {
  List,
  Datagrid,
  TextField,
  NumberField,
  DateField,
  FunctionField,
  SearchInput,
  SelectInput,
} from 'react-admin';
import { Chip } from '@mui/material';
import type { Textbook } from '../../types';

// Фильтры для списка учебников
const textbookFilters = [
  <SearchInput source="q" alwaysOn placeholder="Поиск по названию" key="search" />,
  <SelectInput
    source="subject"
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
    key="subject"
  />,
  <SelectInput
    source="grade_level"
    choices={[
      { id: 7, name: '7 класс' },
      { id: 8, name: '8 класс' },
      { id: 9, name: '9 класс' },
      { id: 10, name: '10 класс' },
      { id: 11, name: '11 класс' },
    ]}
    key="grade_level"
  />,
];

export const TextbookList = () => (
  <List
    filters={textbookFilters}
    sort={{ field: 'created_at', order: 'DESC' }}
    perPage={25}
    title="Глобальные учебники"
  >
    <Datagrid rowClick="show">
      <TextField source="id" label="ID" />
      <TextField source="title" label="Название" />
      <TextField source="subject" label="Предмет" />
      <NumberField source="grade_level" label="Класс" />
      <TextField source="author" label="Автор" emptyText="-" />
      <TextField source="publisher" label="Издательство" emptyText="-" />
      <NumberField source="version" label="Версия" />
      <FunctionField
        label="Статус"
        render={(record: Textbook) => (
          <Chip
            label={record.is_active ? 'Активен' : 'Неактивен'}
            color={record.is_active ? 'success' : 'default'}
            size="small"
          />
        )}
      />
      <DateField
        source="created_at"
        label="Дата создания"
        showTime
        locales="ru-RU"
      />
    </Datagrid>
  </List>
);
