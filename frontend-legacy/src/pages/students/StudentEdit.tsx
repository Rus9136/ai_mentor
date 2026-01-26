import {
  Edit,
  SimpleForm,
  SelectInput,
  DateInput,
  Toolbar,
  SaveButton,
  useRecordContext,
  useNotify,
  useRefresh,
  useRedirect,
  required,
  Button,
} from 'react-admin';
import PersonOffIcon from '@mui/icons-material/PersonOff';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { apiRequest } from '../../providers/dataProvider';
import type { Student } from '../../types';

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
 * Custom Toolbar с кнопками "Сохранить" и "Деактивировать/Активировать"
 */
const StudentEditToolbar = () => {
  const record = useRecordContext<Student>();
  const notify = useNotify();
  const refresh = useRefresh();
  const redirect = useRedirect();

  const handleToggleActive = async () => {
    if (!record) return;

    try {
      const action = record.user?.is_active ? 'deactivate' : 'activate';
      await apiRequest(`/admin/school/students/${record.id}/${action}`, {
        method: 'PATCH',
      });

      notify(
        record.user?.is_active ? 'Ученик деактивирован' : 'Ученик активирован',
        { type: 'success' }
      );
      refresh();
      redirect('show', 'students', record.id);
    } catch (error) {
      notify('Ошибка при изменении статуса ученика', { type: 'error' });
    }
  };

  if (!record) return null;

  return (
    <Toolbar>
      <SaveButton />
      <Button
        label={record.user?.is_active ? 'Деактивировать' : 'Активировать'}
        onClick={handleToggleActive}
        startIcon={record.user?.is_active ? <PersonOffIcon /> : <CheckCircleIcon />}
        sx={{ marginLeft: 2 }}
      />
    </Toolbar>
  );
};

/**
 * Компонент редактирования ученика
 *
 * ВАЖНО: Редактируются только поля Student, НЕ User поля
 * User поля (email, password, name, phone) редактируются отдельно
 *
 * Форма содержит следующие поля:
 * - Код ученика (read-only, нельзя изменить)
 * - Класс* (обязательное, 7-11)
 * - Дата рождения (опциональное)
 * - Дата зачисления (опциональное)
 *
 * Toolbar содержит:
 * - Кнопку "Сохранить" для обновления данных
 * - Кнопку "Деактивировать/Активировать" для изменения статуса user.is_active
 */
export const StudentEdit = () => {
  return (
    <Edit
      redirect="show"
      title="Редактировать ученика"
      mutationMode="pessimistic"
    >
      <SimpleForm toolbar={<StudentEditToolbar />}>
        {/* Код ученика - read-only */}
        <SelectInput
          source="student_code"
          label="Код ученика"
          choices={[]}
          disabled
          fullWidth
          helperText="Код ученика нельзя изменить"
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
          helperText="Дата зачисления в школу (опционально)"
        />
      </SimpleForm>
    </Edit>
  );
};
