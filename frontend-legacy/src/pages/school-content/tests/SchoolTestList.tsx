import { useState } from 'react';
import {
  List,
  Datagrid,
  TextField,
  ReferenceField,
  DateField,
  FunctionField,
  SearchInput,
  SelectInput,
  CreateButton,
  EditButton,
  ShowButton,
  TopToolbar,
} from 'react-admin';
import {
  Box,
  Tabs,
  Tab,
  Chip,
} from '@mui/material';
import type { Test } from '../../../types';

/**
 * SchoolTestList - Библиотека тестов для школьного ADMIN
 *
 * Содержит две вкладки:
 * 1. "Глобальные тесты" (school_id = null) - read-only
 * 2. "Наши тесты" (school_id != null) - полный CRUD
 */

// Фильтры для списка тестов
const testFilters = [
  <SearchInput source="q" alwaysOn placeholder="Поиск по названию" key="search" />,
  <SelectInput
    source="difficulty"
    choices={[
      { id: 'easy', name: 'Легкий' },
      { id: 'medium', name: 'Средний' },
      { id: 'hard', name: 'Сложный' },
    ]}
    key="difficulty"
  />,
];

// Маппинг сложности на русский + цвет
const difficultyLabels: Record<string, { label: string; color: 'success' | 'warning' | 'error' }> = {
  easy: { label: 'Легкий', color: 'success' },
  medium: { label: 'Средний', color: 'warning' },
  hard: { label: 'Сложный', color: 'error' },
};

/**
 * TabPanel компонент для отображения содержимого вкладки
 */
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tests-tabpanel-${index}`}
      aria-labelledby={`tests-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 2 }}>{children}</Box>}
    </div>
  );
}

/**
 * Custom TopToolbar для глобальных тестов (без кнопки Create)
 */
const GlobalTestsActions = () => (
  <TopToolbar>
    {/* Только фильтры, без кнопки Create */}
  </TopToolbar>
);

/**
 * Custom TopToolbar для школьных тестов (с кнопкой Create)
 */
const SchoolTestsActions = () => (
  <TopToolbar>
    <CreateButton label="Создать тест" />
  </TopToolbar>
);

/**
 * Datagrid для глобальных тестов (read-only)
 */
const GlobalTestsDatagrid = () => {
  return (
    <Datagrid bulkActionButtons={false}>
      <TextField source="id" label="ID" />
      <TextField source="title" label="Название" />

      {/* Ссылка на учебник (если есть) */}
      <ReferenceField
        source="textbook_id"
        reference="school-textbooks"
        label="Учебник"
        link="show"
        emptyText="-"
      >
        <TextField source="title" />
      </ReferenceField>

      {/* Ссылка на главу (если есть) */}
      <ReferenceField
        source="chapter_id"
        reference="school-chapters"
        label="Глава"
        link={false}
        emptyText="-"
      >
        <TextField source="title" />
      </ReferenceField>

      <FunctionField
        label="Сложность"
        render={(record: Test) => {
          const config = difficultyLabels[record.difficulty] || {
            label: record.difficulty,
            color: 'default' as const
          };
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
        label="Время выполнения"
        render={(record: Test) =>
          record.time_limit ? `${record.time_limit} мин` : 'Не ограничено'
        }
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

      <DateField source="created_at" label="Создан" showTime locales="ru-RU" />

      {/* Кнопка просмотра */}
      <ShowButton label="Просмотреть" />
    </Datagrid>
  );
};

/**
 * Datagrid для школьных тестов (с полным CRUD)
 */
const SchoolTestsDatagrid = () => {
  return (
    <Datagrid bulkActionButtons={false}>
      <TextField source="id" label="ID" />
      <TextField source="title" label="Название" />

      {/* Ссылка на учебник (если есть) */}
      <ReferenceField
        source="textbook_id"
        reference="school-textbooks"
        label="Учебник"
        link="show"
        emptyText="-"
      >
        <TextField source="title" />
      </ReferenceField>

      {/* Ссылка на главу (если есть) */}
      <ReferenceField
        source="chapter_id"
        reference="school-chapters"
        label="Глава"
        link={false}
        emptyText="-"
      >
        <TextField source="title" />
      </ReferenceField>

      <FunctionField
        label="Сложность"
        render={(record: Test) => {
          const config = difficultyLabels[record.difficulty] || {
            label: record.difficulty,
            color: 'default' as const
          };
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
        label="Время выполнения"
        render={(record: Test) =>
          record.time_limit ? `${record.time_limit} мин` : 'Не ограничено'
        }
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

      <DateField source="created_at" label="Создан" showTime locales="ru-RU" />

      {/* Кнопки редактирования */}
      <EditButton label="Редактировать" />
      <ShowButton label="Просмотреть" />
    </Datagrid>
  );
};

/**
 * Основной компонент SchoolTestList
 */
export const SchoolTestList = () => {
  const [currentTab, setCurrentTab] = useState(0);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  return (
    <Box>
      {/* Заголовок страницы */}
      <Box sx={{ p: 2, pb: 0 }}>
        <h1>Библиотека тестов</h1>
      </Box>

      {/* Tabs навигация */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', px: 2 }}>
        <Tabs value={currentTab} onChange={handleTabChange}>
          <Tab label="Глобальные тесты" id="tests-tab-0" />
          <Tab label="Наши тесты" id="tests-tab-1" />
        </Tabs>
      </Box>

      {/* Вкладка 1: Глобальные тесты */}
      <TabPanel value={currentTab} index={0}>
        <List
          resource="school-tests"
          filter={{ school_id: null }}
          filters={testFilters}
          actions={<GlobalTestsActions />}
          perPage={25}
          sort={{ field: 'created_at', order: 'DESC' }}
          title=" " // Убираем дублирование заголовка
        >
          <GlobalTestsDatagrid />
        </List>
      </TabPanel>

      {/* Вкладка 2: Наши тесты */}
      <TabPanel value={currentTab} index={1}>
        <List
          resource="school-tests"
          filter={{ school_id: 'not_null' }}
          filters={testFilters}
          actions={<SchoolTestsActions />}
          perPage={25}
          sort={{ field: 'created_at', order: 'DESC' }}
          title=" "
        >
          <SchoolTestsDatagrid />
        </List>
      </TabPanel>
    </Box>
  );
};
