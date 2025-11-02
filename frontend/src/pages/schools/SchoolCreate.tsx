import {
  Create,
  SimpleForm,
  TextInput,
  required,
  minLength,
  maxLength,
  regex,
  email,
} from 'react-admin';

/**
 * Валидация поля code
 * - Только lowercase буквы, цифры, дефисы и underscores
 * - Минимум 2 символа, максимум 50
 */
const validateCode = [
  required('Код обязателен для заполнения'),
  minLength(2, 'Код должен содержать минимум 2 символа'),
  maxLength(50, 'Код должен содержать максимум 50 символов'),
  regex(
    /^[a-z0-9_-]+$/,
    'Код должен содержать только lowercase буквы, цифры, дефисы и underscores'
  ),
];

/**
 * Валидация поля name
 */
const validateName = [
  required('Название обязательно для заполнения'),
  maxLength(255, 'Название должно содержать максимум 255 символов'),
];

/**
 * Валидация поля email (опциональное)
 */
const validateEmail = [
  email('Неверный формат email'),
];

/**
 * Валидация поля phone (опциональное)
 */
const validatePhone = [
  maxLength(50, 'Телефон должен содержать максимум 50 символов'),
];

/**
 * Компонент создания новой школы
 *
 * Форма содержит следующие поля:
 * - Название* (обязательное)
 * - Код* (обязательное, уникальное, только lowercase alphanumeric + дефисы/underscores)
 * - Email (опциональное, с валидацией формата)
 * - Телефон (опциональное)
 * - Адрес (опциональное, multiline)
 * - Описание (опциональное, multiline)
 */
export const SchoolCreate = () => {
  return (
    <Create redirect="show" title="Создать школу">
      <SimpleForm>
        <TextInput
          source="name"
          label="Название"
          validate={validateName}
          fullWidth
          helperText="Название школы (например, Школа №1)"
        />

        <TextInput
          source="code"
          label="Код"
          validate={validateCode}
          fullWidth
          helperText="Уникальный код школы (например, school-1). Только lowercase буквы, цифры, дефисы и underscores"
        />

        <TextInput
          source="email"
          label="Email"
          validate={validateEmail}
          type="email"
          fullWidth
          helperText="Email для связи со школой (опционально)"
        />

        <TextInput
          source="phone"
          label="Телефон"
          validate={validatePhone}
          fullWidth
          helperText="Телефон школы (опционально)"
        />

        <TextInput
          source="address"
          label="Адрес"
          multiline
          rows={2}
          fullWidth
          helperText="Физический адрес школы (опционально)"
        />

        <TextInput
          source="description"
          label="Описание"
          multiline
          rows={3}
          fullWidth
          helperText="Дополнительная информация о школе (опционально)"
        />
      </SimpleForm>
    </Create>
  );
};
