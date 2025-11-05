import {
  Edit,
  SimpleForm,
  TextInput,
  SelectInput,
  NumberInput,
  BooleanInput,
  ReferenceInput,
  AutocompleteInput,
  Toolbar,
  SaveButton,
  useRecordContext,
  useNotify,
  useRefresh,
  useRedirect,
  useUpdate,
  required,
  maxLength,
  minValue,
  maxValue,
  Button,
} from 'react-admin';
import { useWatch } from 'react-hook-form';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import BlockIcon from '@mui/icons-material/Block';
import { DifficultyLevel } from '../../types';
import type { Test } from '../../types';

/**
 * Компонент для условного рендеринга зависимых селектов
 * Отслеживает изменения textbook_id и chapter_id через useWatch
 */
const DependentSelects = () => {
  const textbookId = useWatch({ name: 'textbook_id' });
  const chapterId = useWatch({ name: 'chapter_id' });

  return (
    <>
      {/* Глава - показываем только если выбран учебник */}
      <ReferenceInput
        source="chapter_id"
        reference="chapters"
        label="Глава"
        filter={textbookId ? { textbook_id: textbookId } : undefined}
      >
        <AutocompleteInput
          optionText="title"
          filterToQuery={(searchText) => ({ q: searchText })}
          helperText={
            textbookId
              ? 'Выберите главу (опционально)'
              : 'Сначала выберите учебник'
          }
          fullWidth
          disabled={!textbookId}
        />
      </ReferenceInput>

      {/* Параграф - показываем только если выбрана глава */}
      <ReferenceInput
        source="paragraph_id"
        reference="paragraphs"
        label="Параграф"
        filter={chapterId ? { chapter_id: chapterId } : undefined}
      >
        <AutocompleteInput
          optionText="title"
          filterToQuery={(searchText) => ({ q: searchText })}
          helperText={
            chapterId
              ? 'Выберите параграф (опционально)'
              : 'Сначала выберите главу'
          }
          fullWidth
          disabled={!chapterId}
        />
      </ReferenceInput>
    </>
  );
};

/**
 * Валидация поля title
 */
const validateTitle = [
  required('Название обязательно для заполнения'),
  maxLength(255, 'Название должно содержать максимум 255 символов'),
];

/**
 * Валидация поля difficulty
 */
const validateDifficulty = [required('Сложность обязательна для выбора')];

/**
 * Валидация поля passing_score
 */
const validatePassingScore = [
  required('Проходной балл обязателен'),
  minValue(0, 'Проходной балл не может быть меньше 0'),
  maxValue(1, 'Проходной балл не может быть больше 1'),
];

/**
 * Валидация поля time_limit (опциональное)
 */
const validateTimeLimit = [
  minValue(1, 'Время выполнения должно быть минимум 1 минута'),
];

/**
 * Список уровней сложности для выбора
 */
const difficultyChoices = [
  { id: DifficultyLevel.EASY, name: 'Легкий' },
  { id: DifficultyLevel.MEDIUM, name: 'Средний' },
  { id: DifficultyLevel.HARD, name: 'Сложный' },
];

/**
 * Custom Toolbar с кнопками "Сохранить" и "Активировать/Деактивировать"
 */
const TestEditToolbar = () => {
  const record = useRecordContext<Test>();
  const notify = useNotify();
  const refresh = useRefresh();
  const redirect = useRedirect();
  const [update] = useUpdate();

  const handleToggleActive = async () => {
    if (!record) return;

    try {
      await update(
        'tests',
        {
          id: record.id,
          data: { is_active: !record.is_active },
          previousData: record,
        },
        {
          onSuccess: () => {
            notify(
              record.is_active ? 'Тест деактивирован' : 'Тест активирован',
              { type: 'success' }
            );
            refresh();
            redirect('show', 'tests', record.id);
          },
          onError: () => {
            notify('Ошибка при изменении статуса теста', { type: 'error' });
          },
        }
      );
    } catch (error) {
      notify('Ошибка при изменении статуса теста', { type: 'error' });
    }
  };

  if (!record) return null;

  return (
    <Toolbar>
      <SaveButton />
      <Button
        label={record.is_active ? 'Деактивировать' : 'Активировать'}
        onClick={handleToggleActive}
        startIcon={record.is_active ? <BlockIcon /> : <CheckCircleIcon />}
        sx={{ marginLeft: 2 }}
      />
    </Toolbar>
  );
};

/**
 * Компонент редактирования глобального теста
 *
 * Форма содержит следующие поля:
 * - Название* (обязательное)
 * - Описание (опциональное)
 * - Глава (опциональное, связь с chapters)
 * - Параграф (опциональное, связь с paragraphs)
 * - Сложность* (обязательное, выбор из easy/medium/hard)
 * - Время выполнения (опциональное, в минутах)
 * - Проходной балл* (обязательное, 0.0-1.0)
 * - Активен (по умолчанию true)
 *
 * Toolbar содержит:
 * - Кнопку "Сохранить" для обновления данных
 * - Кнопку "Активировать/Деактивировать" для изменения статуса is_active
 */
export const TestEdit = () => {
  return (
    <Edit redirect="show" title="Редактировать глобальный тест">
      <SimpleForm toolbar={<TestEditToolbar />}>
        <TextInput
          source="title"
          label="Название"
          validate={validateTitle}
          fullWidth
          helperText="Название теста (например, Итоговый тест по теме 'Квадратные уравнения')"
        />

        <TextInput
          source="description"
          label="Описание"
          multiline
          rows={3}
          fullWidth
          helperText="Краткое описание теста и его целей (опционально)"
        />

        {/* Каскадные селекты: Учебник → Глава → Параграф */}
        <ReferenceInput
          source="textbook_id"
          reference="textbooks"
          label="Учебник"
        >
          <AutocompleteInput
            optionText="title"
            filterToQuery={(searchText) => ({ q: searchText })}
            helperText="Выберите учебник (опционально)"
            fullWidth
          />
        </ReferenceInput>

        {/* Зависимые селекты для главы и параграфа */}
        <DependentSelects />

        <SelectInput
          source="difficulty"
          label="Сложность"
          choices={difficultyChoices}
          validate={validateDifficulty}
          fullWidth
          helperText="Уровень сложности теста"
        />

        <NumberInput
          source="time_limit"
          label="Время выполнения (минуты)"
          validate={validateTimeLimit}
          fullWidth
          helperText="Ограничение по времени в минутах (опционально, оставьте пустым для неограниченного времени)"
          min={1}
          step={1}
        />

        <NumberInput
          source="passing_score"
          label="Проходной балл"
          validate={validatePassingScore}
          fullWidth
          helperText="Минимальный балл для прохождения теста (от 0 до 1, например 0.7 = 70%)"
          min={0}
          max={1}
          step={0.05}
        />

        <BooleanInput
          source="is_active"
          label="Активен"
          helperText="Активные тесты доступны для прохождения учениками"
        />
      </SimpleForm>
    </Edit>
  );
};
