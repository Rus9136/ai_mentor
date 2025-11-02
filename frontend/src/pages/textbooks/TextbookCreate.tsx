import {
  Create,
  SimpleForm,
  TextInput,
  SelectInput,
  NumberInput,
  required,
  maxLength,
  minValue,
  maxValue,
} from 'react-admin';

/**
 * Валидация поля title
 */
const validateTitle = [
  required('Название обязательно для заполнения'),
  maxLength(255, 'Название должно содержать максимум 255 символов'),
];

/**
 * Валидация поля subject
 */
const validateSubject = [required('Предмет обязателен для выбора')];

/**
 * Валидация поля grade_level
 */
const validateGradeLevel = [required('Класс обязателен для выбора')];

/**
 * Валидация поля year (опциональное)
 */
const validateYear = [
  minValue(1900, 'Год издания не может быть раньше 1900'),
  maxValue(new Date().getFullYear(), 'Год издания не может быть в будущем'),
];

/**
 * Валидация опциональных текстовых полей
 */
const validateOptionalText = [
  maxLength(255, 'Поле должно содержать максимум 255 символов'),
];

/**
 * Список предметов для выбора
 */
const subjectChoices = [
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
];

/**
 * Список классов для выбора
 */
const gradeLevelChoices = [
  { id: 7, name: '7 класс' },
  { id: 8, name: '8 класс' },
  { id: 9, name: '9 класс' },
  { id: 10, name: '10 класс' },
  { id: 11, name: '11 класс' },
];

/**
 * Компонент создания нового глобального учебника
 *
 * Форма содержит следующие поля:
 * - Название* (обязательное)
 * - Предмет* (обязательное, выбор из списка)
 * - Класс* (обязательное, 7-11)
 * - Автор (опциональное)
 * - Издательство (опциональное)
 * - Год издания (опциональное, 1900-текущий год)
 * - ISBN (опциональное)
 * - Описание (опциональное, multiline)
 */
export const TextbookCreate = () => {
  return (
    <Create redirect="show" title="Создать глобальный учебник">
      <SimpleForm>
        <TextInput
          source="title"
          label="Название"
          validate={validateTitle}
          fullWidth
          helperText="Название учебника (например, Алгебра 7 класс)"
        />

        <SelectInput
          source="subject"
          label="Предмет"
          choices={subjectChoices}
          validate={validateSubject}
          fullWidth
          helperText="Выберите предмет из списка"
        />

        <SelectInput
          source="grade_level"
          label="Класс"
          choices={gradeLevelChoices}
          validate={validateGradeLevel}
          fullWidth
          helperText="Выберите класс (7-11)"
        />

        <TextInput
          source="author"
          label="Автор"
          validate={validateOptionalText}
          fullWidth
          helperText="Автор учебника (опционально)"
        />

        <TextInput
          source="publisher"
          label="Издательство"
          validate={validateOptionalText}
          fullWidth
          helperText="Издательство (опционально)"
        />

        <NumberInput
          source="year"
          label="Год издания"
          validate={validateYear}
          fullWidth
          helperText="Год издания учебника (опционально)"
        />

        <TextInput
          source="isbn"
          label="ISBN"
          validate={validateOptionalText}
          fullWidth
          helperText="Международный стандартный книжный номер (опционально)"
        />

        <TextInput
          source="description"
          label="Описание"
          multiline
          rows={4}
          fullWidth
          helperText="Краткое описание учебника (опционально)"
        />
      </SimpleForm>
    </Create>
  );
};
