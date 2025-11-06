import {
  Create,
  SimpleForm,
  TextInput,
  PasswordInput,
  ReferenceArrayInput,
  AutocompleteArrayInput,
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
 * Валидация student_ids
 */
const validateStudentIds = [
  required('Необходимо выбрать хотя бы одного ребенка'),
];

/**
 * Компонент создания нового родителя
 *
 * Transactional форма: создает User + Parent + связи с учениками в одной транзакции
 * Backend автоматически:
 * - Создает User с role=PARENT
 * - Создает Parent с привязкой к User
 * - Создает связи parent_students для выбранных учеников
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
 * Parent поля:
 * - Дети* (обязательное, ReferenceArrayInput для выбора учеников)
 */
export const ParentCreate = () => {
  return (
    <Create redirect="show" title="Добавить родителя">
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
          helperText="Email родителя для входа в систему (должен быть уникальным)"
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
          helperText="Телефон родителя (опционально)"
        />

        {/* Секция: Дети */}
        <Box sx={{ width: '100%', mt: 3, mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            Дети
          </Typography>
          <Divider sx={{ mb: 2 }} />
        </Box>

        <ReferenceArrayInput
          source="student_ids"
          reference="students"
          label="Выберите детей"
          validate={validateStudentIds}
        >
          <AutocompleteArrayInput
            optionText={(record) => {
              const fullName = [
                record.user?.last_name,
                record.user?.first_name,
                record.user?.middle_name,
              ]
                .filter(Boolean)
                .join(' ');
              return `${fullName} (${record.student_code}, ${record.grade_level} класс)`;
            }}
            filterToQuery={(searchText) => ({ q: searchText })}
            fullWidth
            helperText="Выберите одного или нескольких учеников, которые являются детьми этого родителя"
          />
        </ReferenceArrayInput>
      </SimpleForm>
    </Create>
  );
};
