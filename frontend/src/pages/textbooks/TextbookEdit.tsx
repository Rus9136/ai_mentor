import {
  Edit,
  SimpleForm,
  TextInput,
  SelectInput,
  NumberInput,
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
import ArchiveIcon from '@mui/icons-material/Archive';
import UnarchiveIcon from '@mui/icons-material/Unarchive';
import type { Textbook } from '../../types';

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
 * Custom Toolbar с кнопками "Сохранить" и "Архивировать/Восстановить"
 */
const TextbookEditToolbar = () => {
  const record = useRecordContext<Textbook>();
  const notify = useNotify();
  const refresh = useRefresh();
  const redirect = useRedirect();
  const [update] = useUpdate();

  const handleToggleArchive = async () => {
    if (!record) return;

    try {
      await update(
        'textbooks',
        {
          id: record.id,
          data: { is_active: !record.is_active },
          previousData: record,
        },
        {
          onSuccess: () => {
            notify(
              record.is_active ? 'Учебник архивирован' : 'Учебник восстановлен',
              { type: 'success' }
            );
            refresh();
            redirect('show', 'textbooks', record.id);
          },
          onError: () => {
            notify('Ошибка при изменении статуса учебника', { type: 'error' });
          },
        }
      );
    } catch (error) {
      notify('Ошибка при изменении статуса учебника', { type: 'error' });
    }
  };

  if (!record) return null;

  return (
    <Toolbar>
      <SaveButton />
      <Button
        label={record.is_active ? 'Архивировать' : 'Восстановить'}
        onClick={handleToggleArchive}
        startIcon={record.is_active ? <ArchiveIcon /> : <UnarchiveIcon />}
        sx={{ marginLeft: 2 }}
      />
    </Toolbar>
  );
};

/**
 * Компонент редактирования глобального учебника
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
 *
 * Toolbar содержит:
 * - Кнопку "Сохранить" для обновления данных
 * - Кнопку "Архивировать/Восстановить" для изменения статуса is_active
 */
export const TextbookEdit = () => {
  return (
    <Edit redirect="show" title="Редактировать глобальный учебник">
      <SimpleForm toolbar={<TextbookEditToolbar />}>
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
    </Edit>
  );
};
