import {
  Create,
  SimpleForm,
  TextInput,
  SelectInput,
  PasswordInput,
  required,
  minLength,
  maxLength,
  email,
} from 'react-admin';
import { Typography, Divider, Box } from '@mui/material';

/**
 * Валидация email
 */
const validateEmail = [
  required('Email обязателен для заполнения'),
  email('Неверный формат email'),
];

/**
 * Валидация password
 */
const validatePassword = [
  required('Пароль обязателен для заполнения'),
  minLength(8, 'Пароль должен содержать минимум 8 символов'),
];

/**
 * Валидация first_name
 */
const validateFirstName = [
  required('Имя обязательно для заполнения'),
  maxLength(100, 'Имя должно содержать максимум 100 символов'),
];

/**
 * Валидация last_name
 */
const validateLastName = [
  required('Фамилия обязательна для заполнения'),
  maxLength(100, 'Фамилия должна содержать максимум 100 символов'),
];

/**
 * Валидация middle_name (опциональное)
 */
const validateMiddleName = [
  maxLength(100, 'Отчество должно содержать максимум 100 символов'),
];

/**
 * Валидация phone (опциональное)
 */
const validatePhone = [
  maxLength(50, 'Телефон должен содержать максимум 50 символов'),
];

/**
 * Валидация teacher_code (опциональное)
 */
const validateTeacherCode = [
  maxLength(50, 'Код учителя должен содержать максимум 50 символов'),
];

/**
 * Валидация subject
 */
const validateSubject = [
  required('Предмет обязателен для выбора'),
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
 * Компонент создания нового учителя
 *
 * Transactional форма: создает User + Teacher в одной транзакции
 * Backend автоматически:
 * - Создает User с role=TEACHER
 * - Создает Teacher с привязкой к User
 * - Генерирует teacher_code если не указан (формат: TCHR{year}{seq})
 *
 * Форма содержит следующие поля:
 *
 * User поля:
 * - Email* (обязательное, уникальное)
 * - Пароль* (обязательное, минимум 8 символов)
 * - Фамилия* (обязательное)
 * - Имя* (обязательное)
 * - Отчество (опциональное)
 * - Телефон (опциональное)
 *
 * Teacher поля:
 * - Код учителя (опциональное, авто-генерируется если пусто)
 * - Предмет* (обязательное)
 * - Биография (опциональное)
 */
export const TeacherCreate = () => {
  return (
    <Create redirect="show" title="Добавить учителя">
      <SimpleForm>
        {/* Секция: Данные пользователя */}
        <Box sx={{ width: '100%', mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            Данные пользователя
          </Typography>
          <Divider sx={{ mb: 2 }} />
        </Box>

        <TextInput
          source="email"
          label="Email"
          type="email"
          validate={validateEmail}
          fullWidth
          helperText="Email учителя для входа в систему (должен быть уникальным)"
        />

        <PasswordInput
          source="password"
          label="Пароль"
          validate={validatePassword}
          fullWidth
          helperText="Временный пароль для первого входа (минимум 8 символов)"
        />

        <TextInput
          source="last_name"
          label="Фамилия"
          validate={validateLastName}
          fullWidth
        />

        <TextInput
          source="first_name"
          label="Имя"
          validate={validateFirstName}
          fullWidth
        />

        <TextInput
          source="middle_name"
          label="Отчество"
          validate={validateMiddleName}
          fullWidth
          helperText="Опционально"
        />

        <TextInput
          source="phone"
          label="Телефон"
          validate={validatePhone}
          fullWidth
          helperText="Телефон учителя (опционально)"
        />

        {/* Секция: Данные учителя */}
        <Box sx={{ width: '100%', mt: 3, mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            Данные учителя
          </Typography>
          <Divider sx={{ mb: 2 }} />
        </Box>

        <TextInput
          source="teacher_code"
          label="Код учителя"
          validate={validateTeacherCode}
          fullWidth
          helperText="Уникальный код учителя (опционально, будет сгенерирован автоматически если пусто)"
        />

        <SelectInput
          source="subject"
          label="Предмет"
          choices={subjectChoices}
          validate={validateSubject}
          fullWidth
          helperText="Основной предмет преподавания"
        />

        <TextInput
          source="bio"
          label="Биография"
          multiline
          rows={4}
          fullWidth
          helperText="Краткая биография, образование, достижения (опционально)"
        />
      </SimpleForm>
    </Create>
  );
};
