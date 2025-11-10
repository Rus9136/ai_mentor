import {
  Show,
  TextField,
  DateField,
  TabbedShowLayout,
  Tab,
  FunctionField,
  ReferenceField,
  useRecordContext,
  TopToolbar,
  EditButton,
} from 'react-admin';
import { Chip, Alert, Box } from '@mui/material';
import type { Test } from '../../types';
import { QuestionsEditor } from './questions/QuestionsEditor';

// Маппинг сложности на русский + цвет
const difficultyLabels: Record<string, { label: string; color: 'success' | 'warning' | 'error' }> = {
  easy: { label: 'Легкий', color: 'success' },
  medium: { label: 'Средний', color: 'warning' },
  hard: { label: 'Сложный', color: 'error' },
};

/**
 * Компонент вкладки "Вопросы" - обертка для QuestionsEditor
 * Извлекает record через useRecordContext и передает testId в редактор
 */
const QuestionsEditorTab = () => {
  const record = useRecordContext<Test>();

  if (!record) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity="info">Загрузка теста...</Alert>
      </Box>
    );
  }

  // Определяем контекст по URL: если мы на /school-tests, значит школьный ADMIN
  const isSchoolContext = window.location.hash.includes('/school-tests');
  const isGlobalTest = record.school_id === null || record.school_id === undefined;

  // Если школьный ADMIN просматривает глобальный тест, редактор read-only
  const isReadOnly = isSchoolContext && isGlobalTest;

  return (
    <Box sx={{ p: 2 }}>
      <QuestionsEditor testId={record.id} isSchoolTest={isSchoolContext} readOnly={isReadOnly} />
    </Box>
  );
};

/**
 * Компонент для условного отображения кнопки Edit
 */
const TestShowActions = () => {
  const record = useRecordContext<Test>();

  // Определяем контекст: если мы на /school-tests и тест глобальный (school_id = null),
  // то кнопка Edit НЕ должна быть доступна
  const isSchoolContext = window.location.hash.includes('/school-tests');
  const isGlobalTest = record?.school_id === null || record?.school_id === undefined;

  // Школьный ADMIN не может редактировать глобальные тесты
  if (isSchoolContext && isGlobalTest) {
    return <TopToolbar />; // Пустой toolbar без кнопок
  }

  return (
    <TopToolbar>
      <EditButton />
    </TopToolbar>
  );
};

/**
 * Компонент для отображения иерархии теста (Учебник → Глава → Параграф)
 * Динамически выбирает правильный reference в зависимости от контекста (global/school)
 */
const TestHierarchy = () => {
  // Определяем контекст: если мы на /school-tests, используем school-* references
  const isSchoolContext = window.location.hash.includes('/school-tests');

  return (
    <>
      <ReferenceField
        source="textbook_id"
        reference={isSchoolContext ? 'school-textbooks' : 'textbooks'}
        label="Учебник"
        link="show"
        emptyText="Не привязан к учебнику"
      >
        <TextField source="title" />
      </ReferenceField>

      <ReferenceField
        source="chapter_id"
        reference={isSchoolContext ? 'school-chapters' : 'chapters'}
        label="Глава"
        link={false}
        emptyText="Не привязан к главе"
      >
        <TextField source="title" />
      </ReferenceField>

      <ReferenceField
        source="paragraph_id"
        reference={isSchoolContext ? 'school-paragraphs' : 'paragraphs'}
        label="Параграф"
        link={false}
        emptyText="Не привязан к параграфу"
      >
        <TextField source="title" />
      </ReferenceField>
    </>
  );
};

/**
 * Компонент просмотра глобального теста
 *
 * Содержит две вкладки:
 * 1. Информация - метаданные теста
 * 2. Вопросы - редактор вопросов с полным CRUD функционалом
 */
export const TestShow = () => (
  <Show title="Просмотр теста" actions={<TestShowActions />}>
    <TabbedShowLayout>
      {/* Вкладка 1: Информация о тесте */}
      <Tab label="Информация">
        <TextField source="id" label="ID" />

        <TextField source="title" label="Название" />

        <TextField
          source="description"
          label="Описание"
          emptyText="Нет описания"
        />

        {/* Иерархия: Учебник → Глава → Параграф */}
        <TestHierarchy />

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
            record.time_limit ? `${record.time_limit} минут` : 'Не ограничено'
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

        <DateField
          source="created_at"
          label="Дата создания"
          showTime
          locales="ru-RU"
        />

        <DateField
          source="updated_at"
          label="Обновлено"
          showTime
          locales="ru-RU"
        />
      </Tab>

      {/* Вкладка 2: Вопросы - редактор вопросов */}
      <Tab label="Вопросы" path="questions">
        <QuestionsEditorTab />
      </Tab>
    </TabbedShowLayout>
  </Show>
);
