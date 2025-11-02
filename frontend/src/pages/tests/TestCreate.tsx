import {
  Create,
  SimpleForm,
  TextInput,
  SelectInput,
  NumberInput,
  BooleanInput,
  ReferenceInput,
  AutocompleteInput,
  required,
  maxLength,
  minValue,
  maxValue,
} from 'react-admin';
import { DifficultyLevel } from '../../types';

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
 * Компонент создания нового глобального теста
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
 */
export const TestCreate = () => {
  return (
    <Create redirect="show" title="Создать глобальный тест">
      <SimpleForm
        defaultValues={{
          difficulty: DifficultyLevel.MEDIUM,
          passing_score: 0.7,
          is_active: true,
        }}
      >
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

        <ReferenceInput
          source="chapter_id"
          reference="chapters"
          label="Глава"
        >
          <AutocompleteInput
            optionText="title"
            filterToQuery={(searchText) => ({ q: searchText })}
            helperText="К какой главе относится тест (опционально)"
            fullWidth
          />
        </ReferenceInput>

        <ReferenceInput
          source="paragraph_id"
          reference="paragraphs"
          label="Параграф"
        >
          <AutocompleteInput
            optionText="title"
            filterToQuery={(searchText) => ({ q: searchText })}
            helperText="К какому параграфу относится тест (опционально)"
            fullWidth
          />
        </ReferenceInput>

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
          defaultValue={true}
        />
      </SimpleForm>
    </Create>
  );
};
