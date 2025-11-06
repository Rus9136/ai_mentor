import { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  CircularProgress,
} from '@mui/material';
import { useNotify } from 'react-admin';
import { getAuthToken } from '../../providers/authProvider';

const API_URL = 'http://localhost:8000/api/v1';

interface ChapterCreateDialogProps {
  open: boolean;
  textbookId: number;
  onClose: () => void;
  onSuccess: () => void;
  isSchoolTextbook?: boolean;
}

interface ChapterFormData {
  title: string;
  number: number;
  order: number;
  description: string;
  learning_objective: string;
}

/**
 * Диалог создания новой главы
 *
 * Форма содержит поля:
 * - Название* (обязательное)
 * - Номер главы* (обязательное, >= 1)
 * - Порядок* (обязательное, >= 1)
 * - Описание (опциональное)
 * - Цель обучения (опциональное)
 */
export const ChapterCreateDialog = ({
  open,
  textbookId,
  onClose,
  onSuccess,
  isSchoolTextbook = false,
}: ChapterCreateDialogProps) => {
  const [formData, setFormData] = useState<ChapterFormData>({
    title: '',
    number: 1,
    order: 1,
    description: '',
    learning_objective: '',
  });
  const [errors, setErrors] = useState<Partial<Record<keyof ChapterFormData, string>>>({});
  const [submitting, setSubmitting] = useState(false);

  const notify = useNotify();

  // Валидация формы
  const validate = (): boolean => {
    const newErrors: Partial<Record<keyof ChapterFormData, string>> = {};

    if (!formData.title.trim()) {
      newErrors.title = 'Название обязательно для заполнения';
    } else if (formData.title.length > 255) {
      newErrors.title = 'Название должно содержать максимум 255 символов';
    }

    if (formData.number < 1) {
      newErrors.number = 'Номер главы должен быть >= 1';
    }

    if (formData.order < 1) {
      newErrors.order = 'Порядок должен быть >= 1';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Обработчик отправки формы
  const handleSubmit = async () => {
    if (!validate()) {
      return;
    }

    setSubmitting(true);

    try {
      const token = getAuthToken();
      const payload = {
        textbook_id: textbookId,
        title: formData.title.trim(),
        number: formData.number,
        order: formData.order,
        description: formData.description.trim() || undefined,
        learning_objective: formData.learning_objective.trim() || undefined,
      };

      const endpoint = isSchoolTextbook
        ? `${API_URL}/admin/school/chapters`
        : `${API_URL}/admin/global/chapters`;
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка создания главы');
      }

      notify('Глава успешно создана', { type: 'success' });
      onSuccess();
      handleClose();
    } catch (error) {
      notify(
        error instanceof Error ? error.message : 'Ошибка создания главы',
        { type: 'error' }
      );
    } finally {
      setSubmitting(false);
    }
  };

  // Закрытие диалога с очисткой формы
  const handleClose = () => {
    setFormData({
      title: '',
      number: 1,
      order: 1,
      description: '',
      learning_objective: '',
    });
    setErrors({});
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Создать новую главу</DialogTitle>

      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          <TextField
            label="Название главы"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            error={!!errors.title}
            helperText={errors.title || 'Название главы (например, "Линейные уравнения")'}
            required
            fullWidth
            autoFocus
          />

          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              label="Номер главы"
              type="number"
              value={formData.number}
              onChange={(e) => setFormData({ ...formData, number: parseInt(e.target.value) || 1 })}
              error={!!errors.number}
              helperText={errors.number || 'Номер главы в учебнике'}
              required
              fullWidth
              inputProps={{ min: 1 }}
            />

            <TextField
              label="Порядок отображения"
              type="number"
              value={formData.order}
              onChange={(e) => setFormData({ ...formData, order: parseInt(e.target.value) || 1 })}
              error={!!errors.order}
              helperText={errors.order || 'Порядок сортировки'}
              required
              fullWidth
              inputProps={{ min: 1 }}
            />
          </Box>

          <TextField
            label="Описание"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            multiline
            rows={3}
            fullWidth
            helperText="Краткое описание главы (опционально)"
          />

          <TextField
            label="Цель обучения"
            value={formData.learning_objective}
            onChange={(e) => setFormData({ ...formData, learning_objective: e.target.value })}
            multiline
            rows={2}
            fullWidth
            helperText="Учебные цели главы (опционально)"
          />
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} disabled={submitting}>
          Отмена
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          color="primary"
          disabled={submitting}
          startIcon={submitting && <CircularProgress size={16} />}
        >
          {submitting ? 'Создание...' : 'Создать'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
