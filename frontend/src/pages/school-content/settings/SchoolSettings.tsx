/**
 * SchoolSettings Component
 *
 * Компонент для управления настройками школы школьным администратором.
 * Позволяет редактировать контактную информацию и просматривать основные данные.
 */
import { useState, useEffect } from 'react';
import {
  useNotify,
  useGetIdentity,
  Loading
} from 'react-admin';
import {
  Box,
  Typography,
  Paper,
  Divider,
  Alert,
  TextField,
  Button,
  CircularProgress
} from '@mui/material';
import SaveIcon from '@mui/icons-material/Save';
import { getAuthToken } from '../../../providers/authProvider';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

interface School {
  id: number;
  name: string;
  code: string;
  description?: string;
  is_active: boolean;
  email?: string;
  phone?: string;
  address?: string;
  created_at: string;
  updated_at: string;
}

/**
 * SchoolSettings - компонент настроек школы
 */
export const SchoolSettings = () => {
  const { identity: _identity, isLoading: identityLoading } = useGetIdentity();
  const notify = useNotify();
  const [school, setSchool] = useState<School | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Form state
  const [description, setDescription] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');

  // Load school settings
  useEffect(() => {
    const fetchSettings = async () => {
      const token = getAuthToken();
      if (!token) {
        notify('Токен аутентификации не найден', { type: 'error' });
        return;
      }

      try {
        const response = await fetch(`${API_URL}/admin/school/settings`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        setSchool(data);
        setDescription(data.description || '');
        setEmail(data.email || '');
        setPhone(data.phone || '');
        setAddress(data.address || '');
      } catch (error: any) {
        notify(`Ошибка загрузки настроек: ${error.message}`, { type: 'error' });
      } finally {
        setLoading(false);
      }
    };

    if (!identityLoading) {
      fetchSettings();
    }
  }, [identityLoading, notify]);

  const handleSave = async () => {
    const token = getAuthToken();
    if (!token) {
      notify('Токен аутентификации не найден', { type: 'error' });
      return;
    }

    setSaving(true);
    try {
      const response = await fetch(`${API_URL}/admin/school/settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          description,
          email,
          phone,
          address,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setSchool(data);
      notify('Настройки школы успешно обновлены', { type: 'success' });
    } catch (error: any) {
      notify(`Ошибка сохранения: ${error.message}`, { type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  if (identityLoading || loading) {
    return <Loading />;
  }

  if (!school) {
    return (
      <Box p={2}>
        <Alert severity="error">
          Не удалось загрузить настройки школы
        </Alert>
      </Box>
    );
  }

  return (
    <Box p={2}>
      <Typography variant="h4" gutterBottom>
        Настройки школы
      </Typography>

      {/* Секция 1: Основная информация (read-only) */}
      <Paper elevation={1} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom color="primary">
          Основная информация
        </Typography>
        <Divider sx={{ mb: 2 }} />

        <Box display="flex" flexDirection="column" gap={2}>
          <TextField
            label="Название школы"
            value={school.name}
            disabled
            fullWidth
            helperText="Изменить может только суперадминистратор"
          />

          <TextField
            label="Код школы"
            value={school.code}
            disabled
            fullWidth
            helperText="Уникальный код школы"
          />

          <TextField
            label="Описание"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            multiline
            rows={3}
            fullWidth
            helperText="Краткое описание вашей школы"
          />
        </Box>
      </Paper>

      {/* Секция 2: Контактная информация (editable) */}
      <Paper elevation={1} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom color="primary">
          Контактная информация
        </Typography>
        <Divider sx={{ mb: 2 }} />

        <Box display="flex" flexDirection="column" gap={2}>
          <TextField
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            fullWidth
            helperText="Контактный email школы"
          />

          <TextField
            label="Телефон"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            fullWidth
            helperText="Контактный телефон школы"
          />

          <TextField
            label="Адрес"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            multiline
            rows={2}
            fullWidth
            helperText="Физический адрес школы"
          />
        </Box>
      </Paper>

      {/* Секция 3: Параметры обучения (placeholder) */}
      <Paper elevation={1} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom color="primary">
          Параметры обучения
        </Typography>
        <Divider sx={{ mb: 2 }} />

        <Alert severity="info" sx={{ mb: 2 }}>
          Эти параметры будут доступны в следующей версии. Сейчас используются значения по умолчанию.
        </Alert>

        <Box display="flex" flexDirection="column" gap={2}>
          <TextField
            label="Проходной балл по умолчанию (%)"
            value="60"
            disabled
            fullWidth
            helperText="Минимальный процент для прохождения теста"
          />

          <TextField
            label="Ограничение времени по умолчанию (минуты)"
            value="30"
            disabled
            fullWidth
            helperText="Максимальное время на выполнение теста"
          />
        </Box>
      </Paper>

      {/* Секция 4: Интеграции (placeholder) */}
      <Paper elevation={1} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom color="primary">
          Интеграции
        </Typography>
        <Divider sx={{ mb: 2 }} />

        <Alert severity="info">
          Интеграции с внешними системами (API keys, webhooks) будут доступны в будущих версиях.
        </Alert>
      </Paper>

      {/* Save Button */}
      <Box display="flex" justifyContent="flex-end">
        <Button
          variant="contained"
          onClick={handleSave}
          disabled={saving}
          startIcon={saving ? <CircularProgress size={18} color="inherit" /> : <SaveIcon />}
        >
          Сохранить
        </Button>
      </Box>
    </Box>
  );
};
