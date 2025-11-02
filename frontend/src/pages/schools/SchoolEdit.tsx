import {
  Edit,
  SimpleForm,
  TextInput,
  Toolbar,
  SaveButton,
  useRecordContext,
  useNotify,
  useRefresh,
  useRedirect,
  required,
  maxLength,
  email,
  Button,
} from 'react-admin';
import BlockIcon from '@mui/icons-material/Block';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { apiRequest } from '../../providers/dataProvider';
import type { School } from '../../types';

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
const validateEmail = [email('Неверный формат email')];

/**
 * Валидация поля phone (опциональное)
 */
const validatePhone = [
  maxLength(50, 'Телефон должен содержать максимум 50 символов'),
];

/**
 * Custom Toolbar с кнопками "Сохранить" и "Заблокировать/Разблокировать"
 */
const SchoolEditToolbar = () => {
  const record = useRecordContext<School>();
  const notify = useNotify();
  const refresh = useRefresh();
  const redirect = useRedirect();

  const handleToggleBlock = async () => {
    if (!record) return;

    try {
      const action = record.is_active ? 'block' : 'unblock';
      await apiRequest(`/admin/schools/${record.id}/${action}`, {
        method: 'PATCH',
      });

      notify(
        record.is_active ? 'Школа заблокирована' : 'Школа разблокирована',
        { type: 'success' }
      );
      refresh();
      redirect('show', 'schools', record.id);
    } catch (error) {
      notify('Ошибка при изменении статуса школы', { type: 'error' });
    }
  };

  if (!record) return null;

  return (
    <Toolbar>
      <SaveButton />
      <Button
        label={record.is_active ? 'Заблокировать школу' : 'Разблокировать школу'}
        onClick={handleToggleBlock}
        startIcon={record.is_active ? <BlockIcon /> : <CheckCircleIcon />}
        sx={{ marginLeft: 2 }}
      />
    </Toolbar>
  );
};

/**
 * Компонент редактирования школы
 *
 * Форма содержит следующие поля:
 * - Код (read-only, нельзя изменить)
 * - Название* (обязательное)
 * - Email (опциональное, с валидацией формата)
 * - Телефон (опциональное)
 * - Адрес (опциональное, multiline)
 * - Описание (опциональное, multiline)
 *
 * Toolbar содержит:
 * - Кнопку "Сохранить" для обновления данных
 * - Кнопку "Заблокировать/Разблокировать" для изменения статуса
 */
export const SchoolEdit = () => {
  return (
    <Edit redirect="show" title="Редактировать школу">
      <SimpleForm toolbar={<SchoolEditToolbar />}>
        <TextInput
          source="code"
          label="Код"
          disabled
          fullWidth
          helperText="Код школы нельзя изменить после создания"
        />

        <TextInput
          source="name"
          label="Название"
          validate={validateName}
          fullWidth
          helperText="Название школы (например, Школа №1)"
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
    </Edit>
  );
};
