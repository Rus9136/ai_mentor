import {
  Create,
  SimpleForm,
  TextInput,
  SelectInput,
  DateInput,
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
 * Валидация student_code (опциональное)
 */
const validateStudentCode = [
  maxLength(50, 'Код ученика должен содержать максимум 50 символов'),
];

/**
 * Валидация grade_level
 */
const validateGradeLevel = [
  required('Класс обязателен для выбора'),
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
 * Компонент создания нового ученика
 *
 * Transactional форма: создает User + Student в одной транзакции
 * Backend автоматически:
 * - Создает User с role=STUDENT
 * - Создает Student с привязкой к User
 * - Генерирует student_code если не указан (формат: STU{grade}{year}{seq})
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
 * Student поля:
 * - Код ученика (опциональное, авто-генерируется если пусто)
 * - Класс* (обязательное, 7-11)
 * - Дата рождения (опциональное)
 * - Дата зачисления (опциональное, по умолчанию сегодня)
 */
export const StudentCreate = () => {
  return (
    <Create
      redirect="show"
      title="Добавить ученика"
      transform={(data) => ({
        ...data,
        // Если дата зачисления не указана, устанавливаем сегодня
        enrollment_date: data.enrollment_date || new Date().toISOString().split('T')[0],
      })}
    >
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
          helperText="Email ученика для входа в систему (должен быть уникальным)"
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
          helperText="Телефон ученика или родителей (опционально)"
        />

        {/* Секция: Данные ученика */}
        <Box sx={{ width: '100%', mt: 3, mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            Данные ученика
          </Typography>
          <Divider sx={{ mb: 2 }} />
        </Box>

        <TextInput
          source="student_code"
          label="Код ученика"
          validate={validateStudentCode}
          fullWidth
          helperText="Уникальный код ученика (опционально, будет сгенерирован автоматически если пусто)"
        />

        <SelectInput
          source="grade_level"
          label="Класс"
          choices={gradeLevelChoices}
          validate={validateGradeLevel}
          fullWidth
          helperText="Класс обучения (7-11)"
        />

        <DateInput
          source="birth_date"
          label="Дата рождения"
          fullWidth
          helperText="Дата рождения ученика (опционально)"
        />

        <DateInput
          source="enrollment_date"
          label="Дата зачисления"
          fullWidth
          helperText="Дата зачисления в школу (по умолчанию сегодня)"
          defaultValue={new Date().toISOString().split('T')[0]}
        />
      </SimpleForm>
    </Create>
  );
};
