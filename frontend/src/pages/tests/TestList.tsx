import {
  List,
  Datagrid,
  TextField,
  DateField,
  FunctionField,
  SearchInput,
  SelectInput,
  ReferenceField,
  ReferenceInput,
  AutocompleteInput,
  BooleanInput,
} from 'react-admin';
import { Chip } from '@mui/material';
import type { Test } from '../../types';
import { DifficultyLevel } from '../../types';

// Фильтры для списка тестов
const testFilters = [
  <SearchInput
    source="q"
    alwaysOn
    placeholder="Поиск по названию"
    key="search"
  />,
  <ReferenceInput
    source="chapter_id"
    reference="chapters"
    key="chapter"
  >
    <AutocompleteInput
      optionText="title"
      label="Глава"
      filterToQuery={(searchText) => ({ q: searchText })}
    />
  </ReferenceInput>,
  <SelectInput
    source="difficulty"
    choices={[
      { id: DifficultyLevel.EASY, name: 'Легкий' },
      { id: DifficultyLevel.MEDIUM, name: 'Средний' },
      { id: DifficultyLevel.HARD, name: 'Сложный' },
    ]}
    label="Сложность"
    key="difficulty"
  />,
  <BooleanInput
    source="is_active"
    label="Только активные"
    key="is_active"
  />,
];

// Маппинг сложности на русский + цвет
const difficultyLabels: Record<string, { label: string; color: 'success' | 'warning' | 'error' }> = {
  [DifficultyLevel.EASY]: { label: 'Легкий', color: 'success' },
  [DifficultyLevel.MEDIUM]: { label: 'Средний', color: 'warning' },
  [DifficultyLevel.HARD]: { label: 'Сложный', color: 'error' },
};

export const TestList = () => (
  <List
    filters={testFilters}
    sort={{ field: 'created_at', order: 'DESC' }}
    perPage={25}
    title="Глобальные тесты"
  >
    <Datagrid rowClick="show">
      <TextField source="id" label="ID" />
      <TextField source="title" label="Название" />
      <ReferenceField
        source="chapter_id"
        reference="chapters"
        label="Глава"
        link={false}
        emptyText="-"
      >
        <TextField source="title" />
      </ReferenceField>
      <FunctionField
        label="Сложность"
        render={(record: Test) => {
          const config = difficultyLabels[record.difficulty] || { label: record.difficulty, color: 'default' as const };
          return (
            <Chip
              label={config.label}
              color={config.color}
              size="small"
            />
          );
        }}
      />
      <FunctionField
        label="Проходной балл"
        render={(record: Test) => `${Math.round(record.passing_score * 100)}%`}
      />
      <FunctionField
        label="Статус"
        render={(record: Test) => (
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
