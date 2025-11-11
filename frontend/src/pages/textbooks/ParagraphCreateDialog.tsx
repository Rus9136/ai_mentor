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
  Autocomplete,
  Chip,
  Paper,
  IconButton,
  Typography,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import { useNotify } from 'react-admin';
import { getAuthToken } from '../../providers/authProvider';
import type { ParagraphQuestion } from '../../types';

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
  key_terms: string[];
  questions: ParagraphQuestion[];
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
    key_terms: [],
    questions: [],
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
        key_terms: formData.key_terms.length > 0 ? formData.key_terms : undefined,
        questions: formData.questions.length > 0 ? formData.questions : undefined,
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

  // Обработчики для вопросов
  const handleAddQuestion = () => {
    setFormData({
      ...formData,
      questions: [...formData.questions, { order: formData.questions.length + 1, text: '' }],
    });
  };

  const handleRemoveQuestion = (index: number) => {
    const updatedQuestions = formData.questions
      .filter((_, i) => i !== index)
      .map((q, i) => ({ ...q, order: i + 1 }));
    setFormData({ ...formData, questions: updatedQuestions });
  };

  const handleQuestionTextChange = (index: number, text: string) => {
    const updated = [...formData.questions];
    updated[index].text = text;
    setFormData({ ...formData, questions: updated });
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
      key_terms: [],
      questions: [],
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

          <Autocomplete
            multiple
            freeSolo
            options={[]}
            value={formData.key_terms}
            onChange={(_, newValue) => setFormData({ ...formData, key_terms: newValue as string[] })}
            renderTags={(value, getTagProps) =>
              value.map((option, index) => {
                const { key, ...tagProps } = getTagProps({ index });
                return <Chip key={key} label={option} {...tagProps} />;
              })
            }
            renderInput={(params) => (
              <TextField
                {...params}
                label="Ключевые термины"
                placeholder="Введите термин и нажмите Enter"
                helperText='Введите термин и нажмите Enter. Пример: "Жоңғар хандығы", "Қазақ хандығы"'
              />
            )}
          />

          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="subtitle2">Вопросы к параграфу</Typography>
              <Button startIcon={<AddIcon />} size="small" onClick={handleAddQuestion}>
                Добавить вопрос
              </Button>
            </Box>

            {formData.questions.length === 0 ? (
              <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                Пока нет вопросов. Нажмите "Добавить вопрос" чтобы создать первый вопрос.
              </Typography>
            ) : (
              formData.questions.map((q, index) => (
                <Paper key={index} sx={{ p: 2, mb: 1, bgcolor: 'background.default' }}>
                  <Box sx={{ display: 'flex', gap: 2, alignItems: 'start' }}>
                    <Chip label={`#${q.order}`} size="small" color="primary" />
                    <TextField
                      fullWidth
                      multiline
                      rows={2}
                      value={q.text}
                      onChange={(e) => handleQuestionTextChange(index, e.target.value)}
                      placeholder="Текст вопроса"
                    />
                    <IconButton color="error" size="small" onClick={() => handleRemoveQuestion(index)}>
                      <DeleteIcon />
                    </IconButton>
                  </Box>
                </Paper>
              ))
            )}
          </Box>
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
