import {
  Show,
  TextField,
  DateField,
  TabbedShowLayout,
  Tab,
  FunctionField,
  ReferenceField,
} from 'react-admin';
import { Chip, Alert, Box } from '@mui/material';
import type { Test } from '../../types';

// Маппинг сложности на русский + цвет
const difficultyLabels: Record<string, { label: string; color: 'success' | 'warning' | 'error' }> = {
  easy: { label: 'Легкий', color: 'success' },
  medium: { label: 'Средний', color: 'warning' },
  hard: { label: 'Сложный', color: 'error' },
};

/**
 * Компонент просмотра глобального теста
 *
 * Содержит две вкладки:
 * 1. Информация - метаданные теста
 * 2. Вопросы - placeholder для редактора вопросов (будет реализовано в Фазе 2)
 */
export const TestShow = () => (
  <Show title="Просмотр теста">
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

        <ReferenceField
          source="chapter_id"
          reference="chapters"
          label="Глава"
          link={false}
          emptyText="Не привязан к главе"
        >
          <TextField source="title" />
        </ReferenceField>

        <ReferenceField
          source="paragraph_id"
          reference="paragraphs"
          label="Параграф"
          link={false}
          emptyText="Не привязан к параграфу"
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

      {/* Вкладка 2: Вопросы (placeholder для Фазы 2) */}
      <Tab label="Вопросы" path="questions">
        <Box sx={{ p: 2 }}>
          <Alert severity="info">
            Редактор вопросов будет реализован в Фазе 2.
            <br />
            Здесь вы сможете добавлять, редактировать и удалять вопросы теста.
          </Alert>
        </Box>
      </Tab>
    </TabbedShowLayout>
  </Show>
);
