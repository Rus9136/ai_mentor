import {
  Edit,
  SimpleForm,
  TextInput,
  SelectInput,
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
import type { Teacher } from '../../types';

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
 * Custom Toolbar с кнопками "Сохранить" и "Деактивировать/Активировать"
 */
const TeacherEditToolbar = () => {
  const record = useRecordContext<Teacher>();
  const notify = useNotify();
  const refresh = useRefresh();
  const redirect = useRedirect();

  const handleToggleActive = async () => {
    if (!record) return;

    try {
      const action = record.user?.is_active ? 'deactivate' : 'activate';
      await apiRequest(`/admin/school/teachers/${record.id}/${action}`, {
        method: 'PATCH',
      });

      notify(
        record.user?.is_active ? 'Учитель деактивирован' : 'Учитель активирован',
        { type: 'success' }
      );
      refresh();
      redirect('show', 'teachers', record.id);
    } catch (error) {
      notify('Ошибка при изменении статуса учителя', { type: 'error' });
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
 * Компонент редактирования учителя
 *
 * ВАЖНО: Редактируются только поля Teacher, НЕ User поля
 * User поля (email, password, name, phone) редактируются отдельно
 *
 * Форма содержит следующие поля:
 * - Код учителя (read-only, нельзя изменить)
 * - Предмет* (обязательное)
 * - Биография (опциональное)
 *
 * Toolbar содержит:
 * - Кнопку "Сохранить" для обновления данных
 * - Кнопку "Деактивировать/Активировать" для изменения статуса user.is_active
 */
export const TeacherEdit = () => {
  return (
    <Edit
      redirect="show"
      title="Редактировать учителя"
      mutationMode="pessimistic"
    >
      <SimpleForm toolbar={<TeacherEditToolbar />}>
        {/* Код учителя - read-only */}
        <TextInput
          source="teacher_code"
          label="Код учителя"
          disabled
          fullWidth
          helperText="Код учителя нельзя изменить"
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
    </Edit>
  );
};
