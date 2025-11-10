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

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

interface ParagraphCreateDialogProps {
  isSchoolTextbook?: boolean;
  open: boolean;
  chapterId: number;
  onClose: () => void;
  onSuccess: () => void;
}

interface ParagraphFormData {
  title: string;
  number: number;
  order: number;
  content: string;
  summary: string;
  learning_objective: string;
  lesson_objective: string;
}

/**
 * Диалог создания нового параграфа
 *
 * Форма содержит поля:
 * - Название* (обязательное)
 * - Номер параграфа* (обязательное, >= 1)
 * - Порядок* (обязательное, >= 1)
 * - Содержание* (обязательное, textarea)
 * - Краткое описание (опциональное)
 * - Цель обучения (опциональное)
 * - Цель урока (опциональное)
 */
export const ParagraphCreateDialog = ({
  open,
  chapterId,
  onClose,
  onSuccess,
  isSchoolTextbook = false,
}: ParagraphCreateDialogProps) => {
  const [formData, setFormData] = useState<ParagraphFormData>({
    title: '',
    number: 1,
    order: 1,
    content: '',
    summary: '',
    learning_objective: '',
    lesson_objective: '',
  });
  const [errors, setErrors] = useState<Partial<Record<keyof ParagraphFormData, string>>>({});
  const [submitting, setSubmitting] = useState(false);

  const notify = useNotify();

  // Валидация формы
  const validate = (): boolean => {
    const newErrors: Partial<Record<keyof ParagraphFormData, string>> = {};

    if (!formData.title.trim()) {
      newErrors.title = 'Название обязательно для заполнения';
    } else if (formData.title.length > 255) {
      newErrors.title = 'Название должно содержать максимум 255 символов';
    }

    if (formData.number < 1) {
      newErrors.number = 'Номер параграфа должен быть >= 1';
    }

    if (formData.order < 1) {
      newErrors.order = 'Порядок должен быть >= 1';
    }

    if (!formData.content.trim()) {
      newErrors.content = 'Содержание обязательно для заполнения';
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
        chapter_id: chapterId,
        title: formData.title.trim(),
        number: formData.number,
        order: formData.order,
        content: formData.content.trim(),
        summary: formData.summary.trim() || undefined,
        learning_objective: formData.learning_objective.trim() || undefined,
        lesson_objective: formData.lesson_objective.trim() || undefined,
      };

      const response = await fetch(isSchoolTextbook ? `${API_URL}/admin/school/paragraphs` : `${API_URL}/admin/global/paragraphs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка создания параграфа');
      }

      notify('Параграф успешно создан', { type: 'success' });
      onSuccess();
      handleClose();
    } catch (error) {
      notify(
        error instanceof Error ? error.message : 'Ошибка создания параграфа',
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
      content: '',
      summary: '',
      learning_objective: '',
      lesson_objective: '',
    });
    setErrors({});
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>Создать новый параграф</DialogTitle>

      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          <TextField
            label="Название параграфа"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            error={!!errors.title}
            helperText={errors.title || 'Название параграфа (например, "Линейные функции")'}
            required
            fullWidth
            autoFocus
          />

          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              label="Номер параграфа"
              type="number"
              value={formData.number}
              onChange={(e) => setFormData({ ...formData, number: parseInt(e.target.value) || 1 })}
              error={!!errors.number}
              helperText={errors.number || 'Номер параграфа в главе'}
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
            label="Содержание"
            value={formData.content}
            onChange={(e) => setFormData({ ...formData, content: e.target.value })}
            error={!!errors.content}
            helperText={errors.content || 'Основное содержание параграфа (используйте Rich Text Editor для форматирования позже)'}
            multiline
            rows={6}
            required
            fullWidth
          />

          <TextField
            label="Краткое описание"
            value={formData.summary}
            onChange={(e) => setFormData({ ...formData, summary: e.target.value })}
            multiline
            rows={2}
            fullWidth
            helperText="Краткое описание параграфа (опционально)"
          />

          <TextField
            label="Цель обучения"
            value={formData.learning_objective}
            onChange={(e) => setFormData({ ...formData, learning_objective: e.target.value })}
            multiline
            rows={2}
            fullWidth
            helperText="Учебные цели параграфа (опционально)"
          />

          <TextField
            label="Цель урока"
            value={formData.lesson_objective}
            onChange={(e) => setFormData({ ...formData, lesson_objective: e.target.value })}
            multiline
            rows={2}
            fullWidth
            helperText="Цели урока на основе параграфа (опционально)"
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
