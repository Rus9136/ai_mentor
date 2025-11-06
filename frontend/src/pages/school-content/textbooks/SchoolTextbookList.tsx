import { useState } from 'react';
import {
  List,
  Datagrid,
  TextField,
  NumberField,
  DateField,
  FunctionField,
  SearchInput,
  SelectInput,
  CreateButton,
  EditButton,
  ShowButton,
  TopToolbar,
  useListContext,
  useNotify,
  useRedirect,
} from 'react-admin';
import {
  Box,
  Tabs,
  Tab,
  Chip,
  Button,
  Stack,
} from '@mui/material';
import AutoStoriesIcon from '@mui/icons-material/AutoStories';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import type { Textbook } from '../../../types';
import { CustomizeTextbookDialog } from './CustomizeTextbookDialog';

/**
 * SchoolTextbookList - Библиотека учебников для школьного ADMIN
 *
 * Содержит две вкладки:
 * 1. "Глобальные учебники" (school_id = null) - read-only с возможностью кастомизации
 * 2. "Наши учебники" (school_id != null) - полный CRUD
 */

// Фильтры для списка учебников (переиспользуем из TextbookList)
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
      id={`textbooks-tabpanel-${index}`}
      aria-labelledby={`textbooks-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 2 }}>{children}</Box>}
    </div>
  );
}

/**
 * Custom TopToolbar для глобальных учебников (без кнопки Create)
 */
const GlobalTextbooksActions = () => (
  <TopToolbar>
    {/* Только фильтры, без кнопки Create */}
  </TopToolbar>
);

/**
 * Custom TopToolbar для школьных учебников (с кнопкой Create)
 */
const SchoolTextbooksActions = () => (
  <TopToolbar>
    <CreateButton label="Создать учебник" />
  </TopToolbar>
);

/**
 * Datagrid для глобальных учебников (read-only + кнопка Кастомизировать)
 */
const GlobalTextbooksDatagrid = () => {
  const [customizeDialogOpen, setCustomizeDialogOpen] = useState(false);
  const [selectedTextbook, setSelectedTextbook] = useState<Textbook | null>(null);

  const handleCustomizeClick = (record: Textbook) => {
    setSelectedTextbook(record);
    setCustomizeDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setCustomizeDialogOpen(false);
    setSelectedTextbook(null);
  };

  return (
    <>
      <Datagrid bulkActionButtons={false}>
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
        <FunctionField
          label="Действия"
          render={(record: Textbook) => (
            <Stack direction="row" spacing={1}>
              <ShowButton record={record} />
              <Button
                size="small"
                variant="outlined"
                startIcon={<ContentCopyIcon />}
                onClick={(e) => {
                  e.stopPropagation();
                  handleCustomizeClick(record);
                }}
              >
                Кастомизировать
              </Button>
            </Stack>
          )}
        />
      </Datagrid>

      {selectedTextbook && (
        <CustomizeTextbookDialog
          open={customizeDialogOpen}
          onClose={handleCloseDialog}
          textbook={selectedTextbook}
        />
      )}
    </>
  );
};

/**
 * Datagrid для школьных учебников (full CRUD)
 */
const SchoolTextbooksDatagrid = () => {
  return (
    <Datagrid rowClick="edit" bulkActionButtons={false}>
      <TextField source="id" label="ID" />
      <TextField source="title" label="Название" />
      <TextField source="subject" label="Предмет" />
      <NumberField source="grade_level" label="Класс" />
      <TextField source="author" label="Автор" emptyText="-" />
      <NumberField source="version" label="Версия" />
      <FunctionField
        label="Тип"
        render={(record: Textbook) => (
          <Stack direction="row" spacing={1}>
            {record.is_customized && record.global_textbook_id && (
              <Chip
                label={`Адаптирован из ID: ${record.global_textbook_id}`}
                color="info"
                size="small"
                icon={<ContentCopyIcon />}
              />
            )}
            {!record.is_customized && (
              <Chip
                label="Собственный"
                color="default"
                size="small"
                icon={<AutoStoriesIcon />}
              />
            )}
          </Stack>
        )}
      />
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
      <EditButton />
      <ShowButton />
    </Datagrid>
  );
};

/**
 * Главный компонент SchoolTextbookList
 */
export const SchoolTextbookList = () => {
  const [currentTab, setCurrentTab] = useState(0);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  return (
    <Box>
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs value={currentTab} onChange={handleTabChange} aria-label="Вкладки учебников">
          <Tab label="Глобальные учебники" id="textbooks-tab-0" />
          <Tab label="Наши учебники" id="textbooks-tab-1" />
        </Tabs>
      </Box>

      {/* Вкладка 1: Глобальные учебники (school_id = null) */}
      <TabPanel value={currentTab} index={0}>
        <List
          resource="school-textbooks"
          filters={textbookFilters}
          filter={{ school_id: null }}
          sort={{ field: 'created_at', order: 'DESC' }}
          perPage={25}
          title=" "
          actions={<GlobalTextbooksActions />}
          disableSyncWithLocation
        >
          <GlobalTextbooksDatagrid />
        </List>
      </TabPanel>

      {/* Вкладка 2: Наши учебники (school_id != null) */}
      <TabPanel value={currentTab} index={1}>
        <List
          resource="school-textbooks"
          filters={textbookFilters}
          filter={{ school_id: 'not_null' }}
          sort={{ field: 'created_at', order: 'DESC' }}
          perPage={25}
          title=" "
          actions={<SchoolTextbooksActions />}
          disableSyncWithLocation
        >
          <SchoolTextbooksDatagrid />
        </List>
      </TabPanel>
    </Box>
  );
};
