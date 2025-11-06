import {
  Create,
  SimpleForm,
  TextInput,
  SelectInput,
  required,
  minLength,
  maxLength,
  regex,
} from 'react-admin';

/**
 * Валидация name
 */
const validateName = [
  required('Название класса обязательно для заполнения'),
  minLength(2, 'Название должно содержать минимум 2 символа'),
  maxLength(100, 'Название должно содержать максимум 100 символов'),
];

/**
 * Валидация code
 */
const validateCode = [
  required('Код класса обязателен для заполнения'),
  minLength(2, 'Код должен содержать минимум 2 символа'),
  maxLength(50, 'Код должен содержать максимум 50 символов'),
  regex(
    /^[A-Z0-9_-]+$/,
    'Код может содержать только заглавные буквы, цифры, дефис и подчеркивание'
  ),
];

/**
 * Валидация grade_level
 */
const validateGradeLevel = [
  required('Класс обязателен для выбора'),
];

/**
 * Валидация academic_year
 */
const validateAcademicYear = [
  required('Учебный год обязателен для заполнения'),
  regex(
    /^\d{4}\/\d{4}$/,
    'Учебный год должен быть в формате YYYY/YYYY (например, 2024/2025)'
  ),
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
 * Компонент создания нового класса
 *
 * Создает новый класс-группу в школе.
 * Backend автоматически:
 * - Привязывает класс к текущей школе (school_id)
 * - Проверяет уникальность code в пределах школы
 *
 * Форма содержит следующие поля:
 * - Название* (обязательное, 2-100 символов)
 * - Код класса* (обязательное, уникальное, формат: заглавные буквы, цифры, дефис)
 * - Класс* (обязательное, 7-11)
 * - Учебный год* (обязательное, формат: YYYY/YYYY, например 2024/2025)
 */
export const ClassCreate = () => {
  return (
    <Create
      redirect="show"
      title="Добавить класс"
    >
      <SimpleForm>
        <TextInput
          source="name"
          label="Название класса"
          validate={validateName}
          fullWidth
          helperText="Например: 7А, 8Б математика, 10 профиль физмат"
        />

        <TextInput
          source="code"
          label="Код класса"
          validate={validateCode}
          fullWidth
          helperText="Уникальный код класса (заглавные буквы, цифры, дефис). Например: 7A, 8B-MATH, 10-PHYSICS"
        />

        <SelectInput
          source="grade_level"
          label="Класс"
          choices={gradeLevelChoices}
          validate={validateGradeLevel}
          fullWidth
          helperText="Класс обучения (7-11)"
        />

        <TextInput
          source="academic_year"
          label="Учебный год"
          validate={validateAcademicYear}
          fullWidth
          helperText="Формат: YYYY/YYYY (например, 2024/2025)"
          placeholder="2024/2025"
        />
      </SimpleForm>
    </Create>
  );
};
