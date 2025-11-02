import {
  Show,
  SimpleShowLayout,
  TextField,
  EmailField,
  DateField,
  TopToolbar,
  EditButton,
  DeleteButton,
  useRecordContext,
  useNotify,
  useRefresh,
  Button,
} from 'react-admin';
import { Box, Chip } from '@mui/material';
import BlockIcon from '@mui/icons-material/Block';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { apiRequest } from '../../providers/dataProvider';
import type { School } from '../../types';

/**
 * Custom поле для отображения статуса школы
 */
const StatusField = () => {
  const record = useRecordContext<School>();

  if (!record) return null;

  return (
    <Chip
      label={record.is_active ? 'Активна' : 'Заблокирована'}
      color={record.is_active ? 'success' : 'error'}
      size="medium"
      sx={{ fontWeight: 500 }}
    />
  );
};

/**
 * Custom TopToolbar с кнопками действий
 */
const SchoolShowActions = () => {
  const record = useRecordContext<School>();
  const notify = useNotify();
  const refresh = useRefresh();

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
    } catch (error) {
      notify('Ошибка при изменении статуса школы', { type: 'error' });
    }
  };

  if (!record) return null;

  return (
    <TopToolbar>
      <EditButton />
      <Button
        label={record.is_active ? 'Заблокировать' : 'Разблокировать'}
        onClick={handleToggleBlock}
        startIcon={record.is_active ? <BlockIcon /> : <CheckCircleIcon />}
      />
      <DeleteButton
        confirmTitle="Удалить школу"
        confirmContent="Вы уверены, что хотите удалить эту школу? Это действие нельзя отменить."
      />
    </TopToolbar>
  );
};

/**
 * Компонент детального просмотра школы
 *
 * Отображает всю информацию о школе:
 * - ID
 * - Название
 * - Код
 * - Описание
 * - Email
 * - Телефон
 * - Адрес
 * - Статус (активна/заблокирована)
 * - Дата создания
 * - Дата обновления
 *
 * Toolbar содержит:
 * - Кнопку "Редактировать" для перехода к форме редактирования
 * - Кнопку "Заблокировать/Разблокировать" для изменения статуса
 * - Кнопку "Удалить" для удаления школы (soft delete)
 */
export const SchoolShow = () => {
  return (
    <Show actions={<SchoolShowActions />} title="Детали школы">
      <SimpleShowLayout>
        <TextField source="id" label="ID" />
        <TextField source="name" label="Название" />
        <TextField source="code" label="Код" />

        <Box sx={{ marginTop: 2, marginBottom: 2 }}>
          <StatusField />
        </Box>

        <TextField
          source="description"
          label="Описание"
          emptyText="Описание не указано"
        />

        <EmailField source="email" label="Email" emptyText="Email не указан" />
        <TextField
          source="phone"
          label="Телефон"
          emptyText="Телефон не указан"
        />
        <TextField
          source="address"
          label="Адрес"
          emptyText="Адрес не указан"
        />

        <DateField
          source="created_at"
          label="Дата создания"
          showTime
          locales="ru-RU"
        />
        <DateField
          source="updated_at"
          label="Дата обновления"
          showTime
          locales="ru-RU"
        />
      </SimpleShowLayout>
    </Show>
  );
};
